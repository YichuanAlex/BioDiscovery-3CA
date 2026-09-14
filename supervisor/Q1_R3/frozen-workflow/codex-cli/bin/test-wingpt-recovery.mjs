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
        call('read_file',{path:'probe.txt'}),
        call('read_file',{path:'probe.txt'}),
        call('read_file',{path:'probe.txt'}),
        {role:'assistant',content:'RECOVERY_OK'}
      ];
      assert(round <= replies.length);
      if (round === 2) assert(body.messages.at(-1).content.includes('不得猜测或虚报完成'));
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
    process.argv = ['node', 'Qwen3.5-4B.js', '--workspace', ${JSON.stringify(autonomousFixture)}, '--autonomous', '--allow-write', '--allow-shell', '--require-artifact', 'nested/result.txt', 'Build a verified text artifact'];
    let round = 0;
    const call = (name, args) => ({role:'assistant',content:null,tool_calls:[{id:'auto-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    globalThis.fetch = async (_url, options) => {
      const body = JSON.parse(options.body); round++;
      assert(body.tools?.length);
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
      if(round===10)assert(body.messages.at(-1).content.includes('catalog-search limit is reached'));
      let reply;
      if(round<=9)reply=call('search_studies',{query:'__catalog_budget_'+round+'__'});
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
  fs.unlinkSync(taskFile(catalogFixture));
  console.log('PASS: 3CA catalog search budget blocks the ninth unique search and preserves other tools for completion.');
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
} finally {
  fs.rmSync(fixture, { recursive: true, force: true });
}
