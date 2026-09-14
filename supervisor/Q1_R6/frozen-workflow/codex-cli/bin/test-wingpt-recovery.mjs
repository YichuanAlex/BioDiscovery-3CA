import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { createNetworkTools } from "./Qwen3.5-4B-network.js";

const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "Qwen3.5-4B-recovery-"));
const entry = new URL("./Qwen3.5-4B.js", import.meta.url).href;
try {
  fs.writeFileSync(path.join(fixture, "TASK_STATE.md"), "STATE_FIXTURE_PENDING", "utf8");
  const malformed = spawnSync(process.execPath, [fileURLToPath(new URL("./Qwen3.5-4B.js", import.meta.url)), "--prompt-file", path.join(fixture,"TASK_STATE.md"), "unexpected"], {encoding:"utf8",timeout:10000});
  assert.equal(malformed.status,1);assert.match(malformed.stderr,/Do not combine --prompt-file/);
  const child = spawnSync(process.execPath, ["--input-type=module", "-e", `
    import assert from 'node:assert/strict';
    process.argv = ['node', 'Qwen3.5-4B.js', '--workspace', ${JSON.stringify(fixture)}, '--allow-write', '--allow-shell', 'probe'];
    const call = (name, args) => ({role:'assistant', content:null, tool_calls:[{id:String(round),type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    let round = 0;
    globalThis.fetch = async (_url, options) => {
      const body = JSON.parse(options.body);
      assert(body.messages[0].content.includes('STATE_FIXTURE_PENDING'), 'Persisted state must survive a new session');
      round++;
      assert.equal(body.chat_template_kwargs.enable_thinking, round === 1);
      assert(body.tools?.length, 'Recovery and a duplicate call must not disable other tools');
      if (round === 4) assert(body.messages.at(-1).content.includes('exit_code=1'), 'PowerShell errors must not report success');
      const replies = [
        {role:'assistant',content:null},
        call('read_file',{path:'missing.txt'}),
        call('run_powershell',{command:"Get-Item -LiteralPath 'missing-file-for-shell-test.txt'"}),
        call('write_file',{path:'probe.txt',content:'RECOVERY_OK'}),
        call('read_file',{path:'probe.txt',start_line:1,end_line:1}),
        call('read_file',{end_line:1,path:'probe.txt',start_line:1}),
        call('read_file',{start_line:1,end_line:1,path:'probe.txt'}),
        {role:'assistant',content:'RECOVERY_OK'}
      ];
      assert(round <= replies.length);
      if (round === 2) assert(body.messages.at(-1).content.includes('不得猜测或虚报完成'));
      if (round === 7) assert(body.messages.at(-1).content.includes('identical tool call'), 'Argument key order must not bypass duplicate protection');
      if (round === 8) assert(!body.tools.some(tool => tool.function.name === 'read_file'), 'A twice-repeated call must hide only its tool for one response');
      return {ok:true,json:async()=>({choices:[{message:replies[round-1]}]})};
    };
    await import(${JSON.stringify(entry)});
  `], { encoding: "utf8", timeout: 30000 });
  assert.equal(child.status, 0, child.stderr);
  assert.equal(fs.readFileSync(path.join(fixture, "probe.txt"), "utf8"), "RECOVERY_OK");
  assert.match(child.stdout, /Qwen3.5-4B> RECOVERY_OK/);
  console.log("PASS: empty-reply recovery, failed-tool recovery, repeated verification, unchanged-read loop guard, isolated workspace.");
  const autonomousFixture = path.join(fixture, "autonomous");
  fs.mkdirSync(autonomousFixture);
  const automatic = spawnSync(process.execPath, ["--input-type=module", "-e", `
    import assert from 'node:assert/strict';
    import fs from 'node:fs';
    const originalWrite = fs.writeFileSync;
    let checkpointWrites = 0;
    fs.writeFileSync = (file, ...args) => {
      if (String(file).endsWith('.tmp') && String(file).includes('codex-home') && ++checkpointWrites === 2) { const error = new Error('ENOSPC injected transient checkpoint error'); error.code = 'ENOSPC'; throw error; }
      return originalWrite(file, ...args);
    };
    process.argv = ['node', 'Qwen3.5-4B.js', '--workspace', ${JSON.stringify(autonomousFixture)}, '--autonomous', '--allow-write', '--allow-shell', '--require-artifact', 'nested/result.txt', 'Build a verified text artifact at C:/Users/User/Desktop/agentic/task'];
    let round = 0;
    const call = (name, args) => ({role:'assistant',content:null,tool_calls:[{id:'auto-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    globalThis.fetch = async (_url, options) => {
      const body = JSON.parse(options.body); round++;
      assert(body.tools?.length);
      assert(!body.tools.some(tool => tool.function.name === 'computer_use'), 'Unrelated autonomous tasks must not expose Computer Use');
      assert.equal(body.chat_template_kwargs.enable_thinking, true, 'Autonomous recovery must keep thinking enabled');
      const replies = [
        {role:'assistant',content:'I will build it.',reasoning_content:'LOCAL_RETURNED_REASONING_FIXTURE'},
        call('write_file',{path:'nested/result.txt',content:'AUTO_OK'}),
        call('complete_task',{artifacts:['nested/result.txt'],verification_call_id:'not-a-real-call',summary:'premature'}),
        call('run_powershell',{command:"[IO.File]::AppendAllText((Join-Path (Get-Location) 'nested/result.txt'), '_SHELL'); Write-Output VALIDATED"}),
        call('read_file',{path:'nested/result.txt'}),
        call('complete_task',{artifacts:['nested/result.txt'],verification_call_id:'auto-4',summary:'AUTO_VERIFIED'})
      ];
      if(round===2) assert(body.messages.at(-1).content.includes('ENGINE CONTINUATION'));
      if(round===4) assert(body.messages.at(-1).content.startsWith('ERROR:'));
      if(round===6) assert.equal(body.messages.at(-1).content, 'AUTO_OK_SHELL');
      assert(round<=replies.length);
      return {ok:true,json:async()=>({id:'mock-'+round,choices:[{finish_reason:'stop',message:replies[round-1]}],usage:{completion_tokens:10}})};
    };
    await import(${JSON.stringify(entry)});
  `], { encoding: "utf8", timeout: 30000 });
  assert.equal(automatic.status, 0, automatic.stderr);
  assert.equal(fs.readFileSync(path.join(autonomousFixture, "nested", "result.txt"), "utf8"), "AUTO_OK_SHELL");
  assert.match(automatic.stdout, /AUTO_VERIFIED/);
  assert.match(automatic.stderr, /checkpoint-retry.*ENOSPC/);
  const home = fileURLToPath(new URL("../../.runtime/codex-home", import.meta.url));
  const taskFile = (directory) => path.join(home, "tasks", `${createHash("sha256").update(directory.toLowerCase()).digest("hex").slice(0,24)}.json`);
  const jobPath = taskFile(autonomousFixture);
  const job = JSON.parse(fs.readFileSync(jobPath, "utf8"));
  assert.equal(job.status, "completed_candidate");
  const events = fs.readFileSync(job.session_file, "utf8").trim().split("\n").map(JSON.parse);
  const reasoning = events.find((event) => event.payload.type === "reasoning");
  assert.equal(reasoning.payload.content[0].text, "LOCAL_RETURNED_REASONING_FIXTURE");
  assert.equal(reasoning.payload.workflow.raw_fields.reasoning_content, "LOCAL_RETURNED_REASONING_FIXTURE");
  assert.deepEqual(reasoning.payload.summary, []);
  assert(events.some((event) => event.payload.workflow?.event === "model_response"));
  const resumed = spawnSync(process.execPath, [fileURLToPath(new URL("./Qwen3.5-4B.js", import.meta.url)), "--workspace", autonomousFixture, "--autonomous", "--allow-write", "--allow-shell", "--resume"], { encoding: "utf8", timeout: 10000 });
  assert.equal(resumed.status, 0, resumed.stderr);
  assert.match(resumed.stdout, /not rerunning mutations/);
  job.status = "interrupted";
  job.messages.push({role:"assistant",content:null,tool_calls:[{id:"unknown-mutation",type:"function",function:{name:"append_file",arguments:JSON.stringify({path:"nested/result.txt",content:"DUPLICATE"})}}]});
  fs.writeFileSync(jobPath, JSON.stringify(job), "utf8");
  const interrupted = spawnSync(process.execPath, ["--input-type=module", "-e", `
    import assert from 'node:assert/strict';
    process.argv=['node','Qwen3.5-4B.js','--workspace',${JSON.stringify(autonomousFixture)},'--autonomous','--resume','--allow-write','--allow-shell'];
    let round=0;
    globalThis.fetch=async(_url,options)=>{
      const body=JSON.parse(options.body); round++;
      assert(body.messages.some(item=>item.role==='tool'&&item.tool_call_id==='unknown-mutation'&&item.content.includes('result unknown')));
      const name=round===1?'run_powershell':'complete_task';
      const args=round===1?{command:'Write-Output RESUME_VALIDATED'}:{artifacts:['nested/result.txt'],verification_call_id:'resume-1',summary:'RESUME_OK'};
      return {ok:true,json:async()=>({choices:[{message:{role:'assistant',content:null,tool_calls:[{id:'resume-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]}}]})};
    };
    await import(${JSON.stringify(entry)});
  `], {encoding:"utf8",timeout:15000});
  assert.equal(interrupted.status, 0, interrupted.stderr);
  assert.equal(fs.readFileSync(path.join(autonomousFixture, "nested", "result.txt"), "utf8"), "AUTO_OK_SHELL");
  assert.match(interrupted.stdout, /RESUME_OK/);
  const resumedJob = JSON.parse(fs.readFileSync(jobPath, "utf8"));
  const resumedEvents = fs.readFileSync(resumedJob.session_file, "utf8").trim().split("\n").map(JSON.parse);
  assert.equal(resumedEvents[0].type, "session_meta");
  assert(resumedEvents.some((event) => event.payload.workflow?.event === "task_resumed"));
  fs.unlinkSync(jobPath);
  const budgetFixture = path.join(fixture, "budget"); fs.mkdirSync(budgetFixture);
  const budget = spawnSync(process.execPath, ["--input-type=module", "-e", `
    process.argv=['node','Qwen3.5-4B.js','--workspace',${JSON.stringify(budgetFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','1','unfinished probe'];
    globalThis.fetch=async()=>({ok:true,json:async()=>({choices:[{message:{role:'assistant',content:'A plan, not an artifact'}}]})});
    await import(${JSON.stringify(entry)});
  `], {encoding:"utf8",timeout:15000});
  assert.equal(budget.status, 2, budget.stderr);
  const budgetJobPath = taskFile(budgetFixture);
  assert.equal(JSON.parse(fs.readFileSync(budgetJobPath,"utf8")).status,"budget_exhausted"); fs.unlinkSync(budgetJobPath);
  const untilFixture = path.join(fixture, "until-complete"); fs.mkdirSync(untilFixture);
  const untilComplete = spawnSync(process.execPath, ["--input-type=module", "-e", `
    import assert from 'node:assert/strict';
    process.argv=['node','Qwen3.5-4B.js','--workspace',${JSON.stringify(untilFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','0','--require-artifact','done.txt','until complete probe'];
    let round=0;
    const call=(name,args)=>({role:'assistant',content:null,tool_calls:[{id:'until-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    globalThis.fetch=async(_url,options)=>{
      const body=JSON.parse(options.body);round++;
      assert.equal(body.chat_template_kwargs.enable_thinking,true);
      assert(body.messages[0].content.includes('no artificial model-round limit'));
      let reply;
      if(round<=7)reply={role:'assistant',content:'Still planning.'};
      else if(round===8)reply=call('write_file',{path:'done.txt',content:'UNTIL_COMPLETE_OK'});
      else if(round===9)reply=call('run_powershell',{command:"Write-Output UNTIL_COMPLETE_VERIFIED"});
      else reply=call('complete_task',{artifacts:['done.txt'],verification_call_id:'until-9',summary:'UNTIL_COMPLETE_OK'});
      assert(round<=10);
      if(round===8)assert(!body.messages.some(item=>String(item.content||'').includes('Still planning.')),'Loop recovery must discard the repeated recent strategy');
      return {ok:true,json:async()=>({choices:[{message:reply}]})};
    };
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:30000});
  assert.equal(untilComplete.status,0,untilComplete.stderr);
  assert.equal(fs.readFileSync(path.join(untilFixture,'done.txt'),'utf8'),'UNTIL_COMPLETE_OK');
  const untilJobPath=taskFile(untilFixture);
  const untilJob=JSON.parse(fs.readFileSync(untilJobPath,'utf8'));
  assert.equal(untilJob.status,'completed_candidate');
  const untilEvents=fs.readFileSync(untilJob.session_file,'utf8').trim().split('\n').map(JSON.parse);
  assert(untilEvents.some(event=>event.payload.workflow?.event==='loop_recovery'));
  fs.unlinkSync(untilJobPath);
  console.log('PASS: max-rounds 0 survives the old no-action stop and continues until verified completion.');
  const explorationFixture = path.join(fixture, 'exploration'); fs.mkdirSync(explorationFixture);
  const exploration = spawnSync(process.execPath, ['--input-type=module', '-e', `
    import assert from 'node:assert/strict';
    process.argv=['node','Qwen3.5-4B.js','--workspace',${JSON.stringify(explorationFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','0','--require-artifact','done.txt','Build a text artifact at C:/Users/User/Desktop/agentic/task'];
    let round=0;
    globalThis.fetch=async(_url,options)=>{
      const body=JSON.parse(options.body);round++;
      assert(!body.tools.some(tool=>tool.function.name==='computer_use'));
      if(round===13)assert(!body.messages.some(item=>item.role==='tool'&&String(item.content).includes('UNPRODUCTIVE_')),'Successful new shell output must not preserve an endless exploration loop');
      const name=round<=12?'run_powershell':round===13?'write_file':round===14?'run_powershell':'complete_task';
      const args=round<=12?{command:'Write-Output UNPRODUCTIVE_'+round}:round===13?{path:'done.txt',content:'EXPLORATION_OK'}:round===14?{command:'Get-Content -LiteralPath done.txt'}:{artifacts:['done.txt'],verification_call_id:'explore-14',summary:'EXPLORATION_OK'};
      assert(round<=15);
      return {ok:true,json:async()=>({choices:[{message:{role:'assistant',content:null,tool_calls:[{id:'explore-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]}}]})};
    };
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:30000});
  assert.equal(exploration.status,0,exploration.stderr);
  fs.unlinkSync(taskFile(explorationFixture));
  console.log('PASS: Desktop in a path does not expose Computer Use; new shell outputs without workspace writes trigger context recovery.');
  const pathOnlyFixture = path.join(fixture, "path-only"); fs.mkdirSync(pathOnlyFixture);
  const archivePath=path.join(pathOnlyFixture,'asset.tar.gz');fs.writeFileSync(archivePath,'fixture','utf8');
  const pathOnly = spawnSync(process.execPath, ["--input-type=module", "-e", `
    import assert from 'node:assert/strict';
    process.argv=['node','Qwen3.5-4B.js','--workspace',${JSON.stringify(pathOnlyFixture)},'--autonomous','--allow-write','--allow-shell','--require-artifact','done.txt','path-only shell probe'];
    let round=0;
    const call=(name,args)=>({role:'assistant',content:null,tool_calls:[{id:'path-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    globalThis.fetch=async(_url,options)=>{
      const body=JSON.parse(options.body);round++;
      if(round===2){assert(body.messages.at(-1).content.includes('filesystem path alone'));assert(!body.tools.some(tool=>tool.function.name==='run_powershell'));}
      const replies=[call('run_powershell',{command:${JSON.stringify(archivePath + " 2>&1")}}),call('write_file',{path:'done.txt',content:'PATH_GUARD_OK'}),call('run_powershell',{command:'Write-Output PATH_GUARD_VERIFIED'}),call('complete_task',{artifacts:['done.txt'],verification_call_id:'path-3',summary:'PATH_GUARD_OK'})];
      assert(round<=replies.length);
      return {ok:true,json:async()=>({choices:[{message:replies[round-1]}]})};
    };
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:20000});
  assert.equal(pathOnly.status,0,pathOnly.stderr);assert.match(pathOnly.stdout,/PATH_GUARD_OK/);
  fs.unlinkSync(taskFile(pathOnlyFixture));
  console.log('PASS: a bare data path is rejected as a shell no-op and PowerShell is cooled for one response.');
  console.log("PASS: autonomous plan recovery, nested paths, premature completion rejection, shell mutation validation, actual reasoning persistence, resume without mutation replay, unfinished budget nonzero exit.");
  const catalogFixture = path.join(fixture, "catalog-budget"); fs.mkdirSync(catalogFixture);
  const catalogBudget = spawnSync(process.execPath, ["--input-type=module", "-e", `
    import assert from 'node:assert/strict';
    process.argv=['node','Qwen3.5-4B.js','--workspace',${JSON.stringify(catalogFixture)},'--autonomous','--allow-write','--allow-shell','--require-artifact','done.txt','catalog loop probe'];
    let round=0;
    const call=(name,args)=>({role:'assistant',content:null,tool_calls:[{id:'catalog-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    globalThis.fetch=async(_url,options)=>{
      const body=JSON.parse(options.body);round++;
      assert.equal(body.chat_template_kwargs.enable_thinking,true);
      if(round===9)assert(!body.tools.some(tool=>tool.function.name==='search_studies'),'Catalog search must be removed after eight calls');
      if(round===10){assert(body.messages.at(-1).content.includes('catalog-search limit is reached'));assert(!body.tools.some(tool=>tool.function.name==='run_powershell'),'A budget-guarded CLI search must cool PowerShell for one response');}
      if(round===11)assert(body.tools.some(tool=>tool.function.name==='run_powershell'),'Cooled PowerShell must return after one response');
      let reply;
      if(round<=8)reply=call('search_studies',{query:'__catalog_budget_'+round+'__'});
      else if(round===9)reply=call('run_powershell',{command:'threeca.exe search __catalog_budget_9__'});
      else if(round===10)reply=call('write_file',{path:'done.txt',content:'CATALOG_BUDGET_OK'});
      else if(round===11)reply=call('run_powershell',{command:"if ((Get-Content -Raw -LiteralPath 'done.txt') -ne 'CATALOG_BUDGET_OK') { throw 'bad content' }; Write-Output CATALOG_VERIFIED"});
      else reply=call('complete_task',{artifacts:['done.txt'],verification_call_id:'catalog-11',summary:'CATALOG_LIMIT_OK'});
      assert(round<=12);
      return {ok:true,json:async()=>({choices:[{message:reply}]})};
    };
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:30000});
  assert.equal(catalogBudget.status,0,catalogBudget.stderr);
  assert.match(catalogBudget.stdout,/CATALOG_LIMIT_OK/);
  const catalogJobPath=taskFile(catalogFixture);
  assert(JSON.parse(fs.readFileSync(catalogJobPath,'utf8')).observations.some(item=>item.tool==='search_studies'),'Successful source evidence must survive context recovery');
  assert.equal(JSON.parse(fs.readFileSync(catalogJobPath,'utf8')).catalog_searches,8,'Catalog budget must persist across resumes');
  fs.unlinkSync(catalogJobPath);
  console.log('PASS: 3CA catalog budget cools a CLI-search tool for one response and preserves other tools for completion.');
  const formatFixture = path.join(fixture, "formats"); fs.mkdirSync(formatFixture);
  const formats = spawnSync(process.execPath, ["--input-type=module", "-e", `
    import assert from 'node:assert/strict';
    process.argv=['node','Qwen3.5-4B.js','--workspace',${JSON.stringify(formatFixture)},'--autonomous','--allow-write','--allow-shell','format validation probe'];
    let round=0;
    globalThis.fetch=async(_url,options)=>{
      const body=JSON.parse(options.body);round++;
      const replies=[
        ['write_file',{path:'summary.json',content:'{}'}],
        ['write_file',{path:'fake.pdf',content:'not a PDF'}],
        ['run_powershell',{command:'Write-Output FORMAT_CHECK'}],
        ['complete_task',{artifacts:['summary.json','fake.pdf'],verification_call_id:'format-3',summary:'invalid'}],
        ['replace_in_file',{path:'summary.json',old_text:'{}',new_text:'{"ok":true}'}],
        ['run_powershell',{command:'Write-Output FORMAT_RECHECK'}],
        ['complete_task',{artifacts:['summary.json','fake.pdf'],verification_call_id:'format-6',summary:'invalid'}],
        ['complete_task',{artifacts:['summary.json'],verification_call_id:'format-6',summary:'FORMAT_OK'}]
      ];
      if(round===5)assert(body.messages.at(-1).content.includes('Empty/non-object JSON'));
      if(round===8)assert(body.messages.at(-1).content.includes('Invalid/placeholder PDF'));
      assert(round<=replies.length);
      const [name,args]=replies[round-1];
      return {ok:true,json:async()=>({choices:[{message:{role:'assistant',content:null,tool_calls:[{id:'format-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]}}]})};
    };
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:20000});
  assert.equal(formats.status,0,formats.stderr);assert.match(formats.stdout,/FORMAT_OK/);
  const formatJobPath=taskFile(formatFixture);fs.unlinkSync(formatJobPath);
  console.log('PASS: empty JSON and fake PDF completion candidates are rejected; valid nonempty JSON can pass structural verification.');
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async () => ({ status: 200, ok: true,
      headers: new Headers({ "content-type": "text/html" }),
      body: new Response("<title>Cookies</title>Cookies must be enabled Enable cookies and reload this page.").body });
    const network = createNetworkTools(() => ({}));
    await assert.rejects(network.execute("read_webpage", { url: "https://example.com" }), /Access challenge/);
    console.log("PASS: cookie challenge is rejected as unusable evidence.");
  } finally { globalThis.fetch = originalFetch; }
  const staleFixture = path.join(fixture, 'stale-checkpoint'); fs.mkdirSync(staleFixture);
  const staleJobPath = taskFile(staleFixture);
  fs.mkdirSync(path.dirname(staleJobPath), { recursive: true });
  fs.writeFileSync(staleJobPath, JSON.stringify({model:'Qwen3.5-4B',workspace:staleFixture,prompt:'stale probe',required_artifacts:[],phase:'start',next_action:'continue',artifacts:[],evidence:[],observations:[],rounds:0,status:'running',messages:[{role:'system',content:'stale'}]}));
  const stale = spawnSync(process.execPath, ['--input-type=module','-e',`
    import fs from 'node:fs';
    const originalWrite=fs.writeFileSync;
    fs.writeFileSync=(file,...args)=>{if(String(file).endsWith('.tmp')&&String(file).includes('codex-home')){const error=new Error('ENOSPC injected persistent checkpoint error');error.code='ENOSPC';throw error;}return originalWrite(file,...args);};
    process.argv=['node','Qwen3.5-4B.js','--workspace',${JSON.stringify(staleFixture)},'--autonomous','--allow-write','--allow-shell','--resume'];
    globalThis.fetch=async()=>{throw new Error('fetch must not run after checkpoint write failure');};
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:15000});
  assert.equal(stale.status,75,stale.stderr);
  assert.equal(JSON.parse(fs.readFileSync(staleJobPath,'utf8')).status,'running','Failed recovery persistence must leave the last committed checkpoint intact');
  console.log('PASS: persistent checkpoint ENOSPC returns the retryable worker exit code with a stale resumable checkpoint.');
  fs.unlinkSync(staleJobPath);
  const launcherFixture=path.join(fixture,'launcher'); fs.mkdirSync(launcherFixture);
  const launcherWorkspace=path.join(launcherFixture,'task'); fs.mkdirSync(launcherWorkspace);
  const launcherTaskDir=path.join(launcherFixture,'.runtime','codex-home','tasks'); fs.mkdirSync(launcherTaskDir,{recursive:true});
  const launcherHash=createHash('sha256').update(launcherWorkspace.toLowerCase()).digest('hex').slice(0,24);
  fs.writeFileSync(path.join(launcherTaskDir,launcherHash+'.json'),JSON.stringify({workspace:launcherWorkspace,status:'running',last_error:'ENOSPC'}));
  fs.writeFileSync(path.join(launcherTaskDir,'unrelated.json'),'{broken unrelated checkpoint');
  const launcherSource=fs.readFileSync(fileURLToPath(new URL('../../run-Qwen3.5-4B.ps1',import.meta.url)),'utf8')
    .replace(/\$expectedRoot = '[^']*'/,"$expectedRoot = '"+launcherFixture.replaceAll("'","''")+"'")
    .replaceAll("& (Join-Path $PSScriptRoot 'start-Qwen3.5-4B-server.ps1')",'Write-Output MOCK_SERVER_READY')
    .replace(/& \$nodePath \(Join-Path \$PSScriptRoot 'codex-cli\\bin\\codex.js'\) --allow-network @taskArguments/,
      "if ($attempt -eq 1) { $global:LASTEXITCODE = 75 } else { if ($taskArguments -notcontains '--resume') { throw 'Missing --resume' }; $global:LASTEXITCODE = 0 }");
  const launcherScript=path.join(launcherFixture,'run-Qwen3.5-4B.ps1'); fs.writeFileSync(launcherScript,launcherSource);
  for(const name of ['app-server','codex-local.cmd'])fs.writeFileSync(path.join(launcherFixture,name),'fixture');
  const powershell=path.join(process.env.SystemRoot,'System32','WindowsPowerShell','v1.0','powershell.exe');
  const launcherProbe=spawnSync(powershell,['-NoProfile','-File',launcherScript,'--workspace',launcherWorkspace,'--autonomous','--max-rounds','0'],{encoding:'utf8',timeout:15000});
  assert.equal(launcherProbe.status,0,launcherProbe.stderr); assert.match(launcherProbe.stdout,/resuming the same persisted task/);
  const lockProbe=spawnSync(powershell,['-NoProfile','-Command',"$stream=[IO.File]::Open('"+path.join(launcherTaskDir,launcherHash+'.json.runner.lock').replaceAll("'","''")+"',[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None); $stream.Dispose()"],{encoding:'utf8',timeout:10000});
  assert.equal(lockProbe.status,0,lockProbe.stderr);
  console.log('PASS: actual PowerShell launcher resumes stale-running exit 75, ignores unrelated malformed checkpoints, and releases its exclusive lock.');
} finally {
  fs.rmSync(fixture, { recursive: true, force: true });
}
