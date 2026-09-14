import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { createNetworkTools } from "./Qwen3.5-4B-network.js";
import { createThreeCaTools } from "./Qwen3.5-4B-threeca.js";

const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "Qwen3.5-4B-recovery-"));
const entry = new URL("./Qwen3.5-4B.js", import.meta.url).href;
try {
  const workflowRoot=fileURLToPath(new URL('../../',import.meta.url));
  const directoryProbe=fs.mkdtempSync(path.join(workflowRoot,'.threeca','cache','engineering-directory-'));
  try {
    for(let i=0;i<100;i++)fs.writeFileSync(path.join(directoryProbe,`${i}-${'x'.repeat(120)}.csv`),'cell,value\nc1,2\n');
    const threeca=createThreeCaTools((name,_description,properties,required=[])=>({function:{name,parameters:{properties,required}}}),workflowRoot);
    const download=threeca.definitions.find(tool=>tool.function.name==='download_asset');
    const crawl=threeca.definitions.find(tool=>tool.function.name==='crawl_site');
    assert(!Object.hasOwn(download.function.parameters.properties,'max_bytes'));
    assert(!Object.hasOwn(download.function.parameters.properties,'max_extract_bytes'));
    assert(!Object.hasOwn(crawl.function.parameters.properties,'max_pages'));
    const listing=JSON.parse(threeca.execute('inspect_dataset',{path:directoryProbe}));
    assert.equal(listing.format,'directory');assert(listing.entries.length>0&&listing.entries.length<100);assert.equal(listing.entries_truncated,true);
    assert.equal(listing.workflow_truncation.total_entries,100);assert.deepEqual(listing.previews,[]);
    const preview=JSON.parse(threeca.execute('inspect_dataset',{path:path.join(directoryProbe,listing.entries[0].name)}));
    assert.deepEqual(preview.previews[0].columns,['cell','value']);
    assert.throws(()=>threeca.execute('inspect_dataset',{path:fixture}),/leaves the local cache/);
    console.log('PASS: actual project CLI directory listing stays valid bounded JSON; file preview and cache boundary remain enforced.');
  } finally {fs.rmSync(directoryProbe,{recursive:true,force:true});}
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
    import childProcess from 'node:child_process';
    import { syncBuiltinESMExports } from 'node:module';
    const originalSpawn=childProcess.spawnSync;
    let downloads=0;
    const asset={path:'C:/engineering-fixture/actual-archive.tar.gz',source_url:'https://www.dropbox.com/engineering-fixture',sha256:'a'.repeat(64),bytes:12,extraction:{path:'C:/engineering-fixture/extracted'}};
    childProcess.spawnSync=(exe,...args)=>String(exe).endsWith('threeca.exe') ? {status:0,stdout:JSON.stringify(args[0].includes('download') ? (++downloads,asset) : {path:asset.path,sha256:asset.sha256,bytes:asset.bytes}),stderr:''} : originalSpawn(exe,...args);
    syncBuiltinESMExports();
    process.argv=['node','Qwen3.5-4B.js','--workspace',${JSON.stringify(explorationFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','0','--require-artifact','done.txt','Build a text artifact at C:/Users/User/Desktop/agentic/task'];
    let round=0;
    globalThis.fetch=async(_url,options)=>{
      const body=JSON.parse(options.body);round++;
      assert(!body.tools.some(tool=>tool.function.name==='computer_use'));
      if(round===13){
        assert(!body.messages.some(item=>item.role==='tool'&&String(item.content).includes('UNPRODUCTIVE_')),'New shell output must not preserve an endless exploration loop');
        const runtime=JSON.parse(body.messages[0].content.split('Current authoritative engine runtime state:\\n')[1]);
        assert.equal(runtime.asset_references[0].path,asset.path);assert.equal(runtime.asset_references[0].sha256,asset.sha256);
      }
      if(round===14){assert.equal(downloads,1,'Recovery must reuse the actual result rather than download again');assert.match(body.messages.at(-1).content,/EARLIER ACTUAL RESULT/);assert(body.messages.at(-1).content.includes(asset.sha256));}
      if(round===15){const runtime=JSON.parse(body.messages[0].content.split('Current authoritative engine runtime state:\\n')[1]);assert.equal(runtime.asset_references[0].source_url,asset.source_url);assert.equal(runtime.asset_references[0].extraction_path,asset.extraction.path);}
      const name=round===1||round===13?'download_asset':round<=12?'run_powershell':round===14?'get_page':round===15?'write_file':round===16?'run_powershell':'complete_task';
      const args=round===1||round===13?{target:'3ca:engineering-fixture',kind:'data',extract:true}:round<=12?{command:'Write-Output UNPRODUCTIVE_'+round}:round===14?{url_or_path:'engineering-fixture'}:round===15?{path:'done.txt',content:'EXPLORATION_OK'}:round===16?{command:'Get-Content -LiteralPath done.txt'}:{artifacts:['done.txt'],verification_call_id:'explore-16',summary:'EXPLORATION_OK'};
      assert(round<=17);
      return {ok:true,json:async()=>({choices:[{message:{role:'assistant',content:null,tool_calls:[{id:'explore-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]}}]})};
    };
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:30000});
  assert.equal(exploration.status,0,exploration.stderr);
  const explorationJob=JSON.parse(fs.readFileSync(taskFile(explorationFixture),'utf8'));
  assert(explorationJob.tool_results.length<=64);assert.equal(explorationJob.asset_references[0].sha256,'a'.repeat(64));
  const reused=fs.readFileSync(explorationJob.session_file,'utf8').trim().split('\n').map(JSON.parse).find(event=>event.payload.workflow?.event==='tool_result_reused');
  assert.equal(reused.payload.workflow.source_call_id,'explore-1');assert.equal(reused.payload.workflow.current_verification_created,false);
  fs.unlinkSync(taskFile(explorationFixture));
  console.log('PASS: context recovery preserves independent asset references and reuses the actual original result without re-execution or new verification.');
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
  const catalogFixture = path.join(fixture, "catalog-unlimited"); fs.mkdirSync(catalogFixture);
  const catalogUnlimited = spawnSync(process.execPath, ["--input-type=module", "-e", `
    import assert from 'node:assert/strict';
    process.argv=['node','Qwen3.5-4B.js','--workspace',${JSON.stringify(catalogFixture)},'--autonomous','--allow-write','--allow-shell','--require-artifact','done.txt','catalog loop probe'];
    let round=0;
    const call=(name,args)=>({role:'assistant',content:null,tool_calls:[{id:'catalog-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    globalThis.fetch=async(_url,options)=>{
      const body=JSON.parse(options.body);round++;
      assert.equal(body.chat_template_kwargs.enable_thinking,true);
      assert.equal(body.tool_choice,'required');
      assert.equal(body.structured_outputs,undefined);
      assert(body.tools.some(tool=>tool.function.name==='search_studies'),'Catalog search must remain available without a request ceiling');
      let reply;
      if(round<=12)reply=call('search_studies',{query:'__catalog_unlimited_'+round+'__'});
      else if(round===13)reply=call('write_file',{path:'done.txt',content:'CATALOG_UNLIMITED_OK'});
      else if(round===14)reply=call('run_powershell',{command:"if ((Get-Content -Raw -LiteralPath 'done.txt') -ne 'CATALOG_UNLIMITED_OK') { throw 'bad content' }; Write-Output CATALOG_VERIFIED"});
      else reply=call('complete_task',{artifacts:['done.txt'],verification_call_id:'catalog-14',summary:'CATALOG_UNLIMITED_OK'});
      assert(round<=15);
      return {ok:true,json:async()=>({choices:[{message:reply}]})};
    };
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:30000});
  assert.equal(catalogUnlimited.status,0,catalogUnlimited.stderr);
  assert.match(catalogUnlimited.stdout,/CATALOG_UNLIMITED_OK/);
  const catalogJobPath=taskFile(catalogFixture);
  assert(JSON.parse(fs.readFileSync(catalogJobPath,'utf8')).observations.some(item=>item.tool==='search_studies'),'Successful source evidence must survive context recovery');
  assert.equal(JSON.parse(fs.readFileSync(catalogJobPath,'utf8')).catalog_searches,12,'Catalog request count is a metric, not a ceiling');
  fs.unlinkSync(catalogJobPath);
  console.log('PASS: native tool calls and 3CA catalog searches remain available beyond the former request ceiling.');
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
        ['run_powershell',{command:'Write-Output FORMAT_FINAL'}],
        ['complete_task',{artifacts:['summary.json'],verification_call_id:'format-8',summary:'FORMAT_OK'}]
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
  const structuredFixture = path.join(fixture, 'truncated-action-recovery'); fs.mkdirSync(structuredFixture);
  const structured = spawnSync(process.execPath, ['--input-type=module','-e',`
    import assert from 'node:assert/strict';
    import fs from 'node:fs';
    process.argv=['node','Qwen3.5-4B.js','--workspace',${JSON.stringify(structuredFixture)},'--allow-write','--allow-shell','--autonomous','--max-rounds','0','--require-artifact','done.txt','structured engineering probe'];
    let round=0;
    globalThis.fetch=async(_url,options)=>{
      const body=JSON.parse(options.body);round++;
      assert.equal(body.tool_choice,'required');
      assert.equal(body.structured_outputs,undefined);
      if(round===1)return {ok:true,json:async()=>({choices:[{finish_reason:'length',message:{role:'assistant',content:'{"name":"run_powershell","arguments":{"command":"Get-ChildItem'}}]})};
      if(round===2){assert(body.messages.at(-1).content.includes('previous structured action reached the generation length'));assert(!body.messages.slice(1,-1).some(item=>String(item.content||'').includes('Get-ChildItem')));return {ok:true,json:async()=>({choices:[{finish_reason:'stop',message:{role:'assistant',content:null,tool_calls:[{id:'recover-2',type:'function',function:{name:'write_file',arguments:JSON.stringify({path:'done.txt',content:'TRUNCATION_RECOVERED'})}}]}}]})};}
      if(round===3)return {ok:true,json:async()=>({choices:[{message:{role:'assistant',content:null,tool_calls:[{id:'recover-3',type:'function',function:{name:'run_powershell',arguments:JSON.stringify({command:'Get-Content -LiteralPath done.txt'})}}]}}]})};
      assert.equal(round,4);
      return {ok:true,json:async()=>({choices:[{message:{role:'assistant',content:null,tool_calls:[{id:'recover-4',type:'function',function:{name:'complete_task',arguments:JSON.stringify({artifacts:['done.txt'],verification_call_id:'recover-3',summary:'TRUNCATION_RECOVERED'})}}]}}]})};
    };
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:30000});
  assert.equal(structured.status,0,structured.stderr);assert.match(structured.stdout,/TRUNCATION_RECOVERED/);
  const structuredJobPath=taskFile(structuredFixture), structuredJob=JSON.parse(fs.readFileSync(structuredJobPath,'utf8'));
  assert.equal(fs.readFileSync(path.join(structuredFixture,'done.txt'),'utf8'),'TRUNCATION_RECOVERED');
  const structuredEvents=fs.readFileSync(structuredJob.session_file,'utf8').trim().split('\n').map(JSON.parse);
  assert(structuredEvents.some(event=>event.payload.workflow?.event==='loop_recovery'&&event.payload.workflow.reason==='truncated_structured_action'));
  assert(structuredEvents.some(event=>event.payload.workflow?.event==='model_request'&&event.payload.workflow.action_mode==='native_function_call'));
  fs.unlinkSync(structuredJobPath);
  console.log('PASS: truncated legacy actions are discarded and retried as concise native function calls.');
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
  const actualLauncherSource=fs.readFileSync(fileURLToPath(new URL('../../run-Qwen3.5-4B.ps1',import.meta.url)),'utf8');
  assert.ok(actualLauncherSource.includes('.runtime\\node-v24.21.0-win-x64\\node.exe'),'Windows agent launcher must use the fixed project-local Node runtime');
  assert.match(actualLauncherSource,/& \$nodePath --no-maglev .*codex\.js/,'Windows agent launcher must disable the crashing Maglev tier');
  const launcherSource=actualLauncherSource
    .replace(/\$expectedRoot = '[^']*'/,"$expectedRoot = '"+launcherFixture.replaceAll("'","''")+"'")
    .replaceAll("& (Join-Path $PSScriptRoot 'start-Qwen3.5-4B-server.ps1')",'Write-Output MOCK_SERVER_READY')
    .replace(/& \$nodePath --no-maglev \(Join-Path \$PSScriptRoot 'codex-cli\\bin\\codex.js'\) --allow-network @taskArguments/,
      "if ($attempt -eq 1) { $global:LASTEXITCODE = 75 } else { if ($taskArguments -notcontains '--resume') { throw 'Missing --resume' }; $global:LASTEXITCODE = 0 }");
  const launcherScript=path.join(launcherFixture,'run-Qwen3.5-4B.ps1'); fs.writeFileSync(launcherScript,launcherSource);
  for(const name of ['app-server','codex-local.cmd'])fs.writeFileSync(path.join(launcherFixture,name),'fixture');
  const launcherNode=path.join(launcherFixture,'.runtime','node-v24.21.0-win-x64','node.exe'); fs.mkdirSync(path.dirname(launcherNode),{recursive:true}); fs.writeFileSync(launcherNode,'fixture');
  const powershell=path.join(process.env.SystemRoot,'System32','WindowsPowerShell','v1.0','powershell.exe');
  const launcherProbe=spawnSync(powershell,['-NoProfile','-File',launcherScript,'--workspace',launcherWorkspace,'--autonomous','--max-rounds','0'],{encoding:'utf8',timeout:15000});
  assert.equal(launcherProbe.status,0,launcherProbe.stderr); assert.match(launcherProbe.stdout,/resuming the same persisted task/);
  const lockProbe=spawnSync(powershell,['-NoProfile','-Command',"$stream=[IO.File]::Open('"+path.join(launcherTaskDir,launcherHash+'.json.runner.lock').replaceAll("'","''")+"',[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None); $stream.Dispose()"],{encoding:'utf8',timeout:10000});
  assert.equal(lockProbe.status,0,lockProbe.stderr);
  console.log('PASS: actual PowerShell launcher resumes stale-running exit 75, ignores unrelated malformed checkpoints, and releases its exclusive lock.');
} finally {
  fs.rmSync(fixture, { recursive: true, force: true });
}
