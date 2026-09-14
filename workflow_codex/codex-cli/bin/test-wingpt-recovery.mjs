import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { createNetworkTools } from "./wingpt-network.js";
import { createThreeCaTools } from "./wingpt-threeca.js";

const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "wingpt-recovery-"));
const entry = new URL("./wingpt.js", import.meta.url).href;
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
  const malformed = spawnSync(process.execPath, [fileURLToPath(new URL("./wingpt.js", import.meta.url)), "--prompt-file", path.join(fixture,"TASK_STATE.md"), "unexpected"], {encoding:"utf8",timeout:10000});
  assert.equal(malformed.status,1);assert.match(malformed.stderr,/Do not combine --prompt-file/);
  const child = spawnSync(process.execPath, ["--input-type=module", "-e", `
    import assert from 'node:assert/strict';
    process.argv = ['node', 'wingpt.js', '--workspace', ${JSON.stringify(fixture)}, '--allow-write', '--allow-shell', 'probe'];
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
      if (round === 8) assert(body.tools.some(tool => tool.function.name === 'read_file'), 'Authorized workspace inspection must remain available after a duplicate call');
      return {ok:true,json:async()=>({choices:[{message:replies[round-1]}]})};
    };
    await import(${JSON.stringify(entry)});
  `], { encoding: "utf8", timeout: 30000 });
  assert.equal(child.status, 0, child.stderr);
  assert.equal(fs.readFileSync(path.join(fixture, "probe.txt"), "utf8"), "RECOVERY_OK");
  assert.match(child.stdout, /WiNGPT> RECOVERY_OK/);
  console.log("PASS: empty-reply recovery, failed-tool recovery, repeated verification, unchanged-read loop guard, isolated workspace.");
  const contextFixture = path.join(fixture, "context-compaction"); fs.mkdirSync(contextFixture);
  for (let index=1;index<=16;index++) fs.writeFileSync(path.join(contextFixture,`large-${index}.txt`),`${index}:`+'x'.repeat(59990),'utf8');
  const context = spawnSync(process.execPath, ["--input-type=module", "-e", `
    import assert from 'node:assert/strict';
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(contextFixture)},'--max-rounds','25','context compaction probe'];
    let round=0;
    globalThis.fetch=async(_url,options)=>{
      const body=JSON.parse(options.body);round++;
      const envelopes=body.messages.filter(item=>item.role==='user'&&String(item.content||'').startsWith('Original task:\\n'));
      assert(envelopes.length<=1,'Compacted context must not retain nested copies of its own envelope');
      if(round>2)assert(JSON.stringify(body.messages).length<900000,'Recent tool results must stay inside the configured model context budget');
      const message=round<=16?{role:'assistant',content:null,tool_calls:[{id:'context-'+round,type:'function',function:{name:'read_file',arguments:JSON.stringify({path:'large-'+round+'.txt'})}}]}:{role:'assistant',content:'CONTEXT_COMPACTION_OK'};
      return {ok:true,json:async()=>({choices:[{message}]})};
    };
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:30000});
  assert.equal(context.status,0,context.stderr);assert.match(context.stdout,/CONTEXT_COMPACTION_OK/);
  console.log('PASS: repeated context compaction retains one authoritative envelope and bounded recent tool evidence.');
  const auditGuardFixture=path.join(fixture,'audited-python-execution');fs.mkdirSync(auditGuardFixture);
  const pythonExecutable=path.join(fileURLToPath(new URL('../../',import.meta.url)),'tools','tool43CA','.venv','Scripts','python.exe');
  const auditGuard=spawnSync(process.execPath,['--input-type=module','-e',`
    import assert from 'node:assert/strict';
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(auditGuardFixture)},'--allow-write','--allow-shell','--max-rounds','12','audited Python execution probe'];
    let round=0;const call=(name,args)=>({role:'assistant',content:null,tool_calls:[{id:'audit-guard-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    const execute={command:${JSON.stringify(`& '${pythonExecutable}' 'valid.py'`)}};
    globalThis.fetch=async(_url,options)=>{const body=JSON.parse(options.body);round++;
      if(round===3)assert.match(body.messages.at(-1).content,/audit_analysis_code successfully/);
      if(round===4)assert.equal(JSON.parse(body.messages.at(-1).content).valid,true);
      if(round===5){assert.match(body.messages.at(-1).content,/1/);assert.match(body.messages.at(-1).content,/exit_code=0/);}
      if(round===7)assert.match(body.messages.at(-1).content,/audit_analysis_code successfully/,'A file mutation must invalidate the earlier audit hash');
      const replies=[call('write_file',{path:'valid.py',content:'print(1)\\n'}),call('run_powershell',execute),call('audit_analysis_code',{path:'valid.py'}),call('run_powershell',execute),call('write_file',{path:'valid.py',content:'print(2)\\n'}),call('run_powershell',execute),{role:'assistant',content:'AUDITED_PYTHON_GUARD_OK'}];
      assert(round<=replies.length);return {ok:true,json:async()=>({choices:[{message:replies[round-1]}]})};};
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:30000});
  assert.equal(auditGuard.status,0,auditGuard.stderr+auditGuard.stdout);assert.match(auditGuard.stdout,/AUDITED_PYTHON_GUARD_OK/);
  console.log('PASS: workspace Python execution requires a successful audit of the exact current file hash.');
  const researchPythonFixture=path.join(fixture,'research-python-before-core');fs.mkdirSync(researchPythonFixture);
  const researchPython=spawnSync(process.execPath,['--input-type=module','-e',`
    import assert from 'node:assert/strict';
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(researchPythonFixture)},'--allow-write','--allow-shell','--require-artifact','results/analysis_manifest.json','--max-rounds','8','research Python before core probe'];
    let round=0;const call=(name,args)=>({role:'assistant',content:null,tool_calls:[{id:'research-python-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    globalThis.fetch=async(_url,options)=>{const body=JSON.parse(options.body);round++;
      if(round===4)assert.match(body.messages.at(-1).content,/call analyze_metabolic_states/);
      const replies=[call('write_file',{path:'analysis.py',content:'print(1)\\n'}),call('audit_analysis_code',{path:'analysis.py'}),call('run_powershell',{command:${JSON.stringify(`& '${pythonExecutable}' 'analysis.py'`)}}),{role:'assistant',content:'RESEARCH_CORE_FIRST_GUARD_OK'}];
      assert(round<=replies.length);return {ok:true,json:async()=>({choices:[{message:replies[round-1]}]})};};
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:30000});
  assert.equal(researchPython.status,0,researchPython.stderr+researchPython.stdout);assert.match(researchPython.stdout,/RESEARCH_CORE_FIRST_GUARD_OK/);
  console.log('PASS: research runs cannot execute custom Python before the vetted core result exists.');
  const directoryStampFixture=path.join(fixture,'empty-directory-stamp');fs.mkdirSync(directoryStampFixture);
  const directoryStamp=spawnSync(process.execPath,['--input-type=module','-e',`
    import assert from 'node:assert/strict';
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(directoryStampFixture)},'--allow-shell','--max-rounds','8','empty directory stamp probe'];
    let round=0;const call=(command)=>({role:'assistant',content:null,tool_calls:[{id:'directory-'+round,type:'function',function:{name:'run_powershell',arguments:JSON.stringify({command})}}]});const inspect="Get-ChildItem -LiteralPath 'empty-marker'";
    globalThis.fetch=async(_url,options)=>{const body=JSON.parse(options.body);round++;
      if(round===4){assert.match(body.messages.at(-1).content,/exit_code=0/);assert.doesNotMatch(body.messages.at(-1).content,/EARLIER ACTUAL RESULT/);}
      const replies=[call(inspect),call("New-Item -ItemType Directory -Path 'empty-marker'"),call(inspect),{role:'assistant',content:'EMPTY_DIRECTORY_STAMP_OK'}];
      assert(round<=replies.length);return {ok:true,json:async()=>({choices:[{message:replies[round-1]}]})};};
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:30000});
  assert.equal(directoryStamp.status,0,directoryStamp.stderr+directoryStamp.stdout);assert.match(directoryStamp.stdout,/EMPTY_DIRECTORY_STAMP_OK/);
  console.log('PASS: empty-directory mutations advance workspace state so a prior known failure can be retried.');
  const claimedValidationFixture=path.join(fixture,'claimed-validation-noop');fs.mkdirSync(claimedValidationFixture);
  const claimedValidation=spawnSync(process.execPath,['--input-type=module','-e',`
    import assert from 'node:assert/strict';
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(claimedValidationFixture)},'--allow-shell','--max-rounds','4','claimed validation no-op probe'];
    let round=0;globalThis.fetch=async(_url,options)=>{const body=JSON.parse(options.body);round++;
      if(round===2)assert.match(body.messages.at(-1).content,/status message does not compile or validate/i);
      const replies=[{role:'assistant',content:null,tool_calls:[{id:'claimed-'+round,type:'function',function:{name:'run_powershell',arguments:JSON.stringify({command:'$pdfFile = "report/main.pdf"; Write-Host "Validating bundle"; $pdfFile'})}}]},{role:'assistant',content:'CLAIMED_VALIDATION_NOOP_OK'}];
      return {ok:true,json:async()=>({choices:[{message:replies[round-1]}]})};};
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:30000});
  assert.equal(claimedValidation.status,0,claimedValidation.stderr+claimedValidation.stdout);assert.match(claimedValidation.stdout,/CLAIMED_VALIDATION_NOOP_OK/);
  console.log('PASS: status-only shell messages cannot masquerade as compilation or validation.');
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
    process.argv = ['node', 'wingpt.js', '--workspace', ${JSON.stringify(autonomousFixture)}, '--autonomous', '--allow-write', '--allow-shell', '--require-artifact', 'nested/result.txt', 'Build a verified text artifact at C:/Users/User/Desktop/agentic/task'];
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
  const milestoneFixture=path.join(fixture,'research-milestone');
  fs.mkdirSync(path.join(milestoneFixture,'results','core_analysis'),{recursive:true});
  fs.mkdirSync(path.join(milestoneFixture,'results','cd8_analysis'),{recursive:true});
  fs.mkdirSync(path.join(milestoneFixture,'sources','literature'),{recursive:true});
  fs.mkdirSync(path.join(milestoneFixture,'inputs'),{recursive:true});
  const milestoneFacts={facts:{cells_analyzed:58843,metabolic_genes_analyzed:1646,selected_resolution:0.8,n_clusters:17,cluster_size_summary:{minimum_cells:714,maximum_cells:8806},metrics:{silhouette:0.2166},random_control_comparison:{metabolic_matched_kmeans_silhouette:0.2201,random_controls_exceeding_or_equal:2,random_controls_total:19,add_one_rank_fraction:0.15},within_replicate_summary:{global_vs_within_ari_min:0.0708,global_vs_within_ari_max:0.676},categorical_confounder_nmi:{patient:0.518,cell_type:0.496,cell_subtype:0.648},conclusion:'inconclusive'}};
  fs.writeFileSync(path.join(milestoneFixture,'results','core_analysis','core_result.json'),JSON.stringify(milestoneFacts));
  fs.writeFileSync(path.join(milestoneFixture,'results','cd8_analysis','core_result.json'),JSON.stringify(milestoneFacts));
  fs.writeFileSync(path.join(milestoneFixture,'sources','literature','verified.json'),JSON.stringify({doi:'10.1/fixture'}));
  fs.writeFileSync(path.join(milestoneFixture,'inputs','staging_manifest.json'),'{}');
  const milestoneCheck=spawnSync(process.execPath,['--input-type=module','-e',`
    import assert from 'node:assert/strict';
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(milestoneFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','1','--require-artifact','results/core_analysis/core_result.json','--require-artifact','results/cd8_analysis/core_result.json','--require-artifact','results/analysis_manifest.json','--require-artifact','report/main.tex','--require-artifact','report/main.pdf','--require-artifact','README.md','research milestone probe'];
    globalThis.fetch=async(_url,options)=>{const body=JSON.parse(options.body);const runtime=JSON.parse(body.messages[0].content.split('Current authoritative engine runtime state:\\n')[1]);assert.equal(runtime.phase,'report_and_manifest');assert.match(runtime.next_required_action,/Create the missing deliverable now with write_file/);assert(runtime.next_required_action.includes('resolution=0.8'));assert(runtime.next_required_action.includes('10.1/fixture'));return {ok:true,json:async()=>({choices:[{message:{role:'assistant',content:null,tool_calls:[{id:'milestone-1',type:'function',function:{name:'write_file',arguments:JSON.stringify({path:'results/analysis_manifest.json',content:'{}'})}}]}}]})};};
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:15000});
  assert.equal(milestoneCheck.status,2,milestoneCheck.stderr+milestoneCheck.stdout);
  const milestoneJob=JSON.parse(fs.readFileSync(taskFile(milestoneFixture),'utf8'));
  assert.equal(milestoneJob.phase,'report_and_manifest');
  assert.match(milestoneJob.next_action,/report\/main.tex/);
  fs.unlinkSync(taskFile(milestoneFixture));
  console.log('PASS: research artifact milestones survive missing model checkpoints and expose the next required action.');
  const sourceFixture=path.join(fixture,'research-source-routing');fs.mkdirSync(sourceFixture);
  const sourceRouting=spawnSync(process.execPath,['--input-type=module','-e',`
    import assert from 'node:assert/strict';
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(sourceFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','2','--require-artifact','results/analysis_manifest.json','--require-artifact','results/core_analysis/core_result.json','use fixed study 3ca:20773'];
    let round=0;globalThis.fetch=async(_url,options)=>{const body=JSON.parse(options.body);round++;const runtime=JSON.parse(body.messages[0].content.split('Current authoritative engine runtime state:\\n')[1]);
      if(round===1){assert.equal(runtime.phase,'source_discovery');assert(body.tools.map(item=>item.function.name).includes('search_studies'));assert(body.tools.map(item=>item.function.name).includes('read_file'));assert(body.tools.map(item=>item.function.name).includes('run_powershell'));assert(!body.tools.map(item=>item.function.name).includes('get_study'));return {ok:true,json:async()=>({choices:[{message:{role:'assistant',content:null,tool_calls:[{id:'source-1',type:'function',function:{name:'search_studies',arguments:JSON.stringify({query:'__research_source_routing__'})}}]}}]})};}
      assert.equal(runtime.phase,'source_selection');assert.match(runtime.next_required_action,/3ca:20773/);assert(body.tools.map(item=>item.function.name).includes('get_study'));assert(body.tools.map(item=>item.function.name).includes('read_file'));assert(body.tools.map(item=>item.function.name).includes('write_file'));assert(!body.tools.map(item=>item.function.name).includes('plan_asset'));return {ok:true,json:async()=>({choices:[{message:{role:'assistant',content:'SOURCE_ROUTING_CHECKED'}}]})};};
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:15000});
  assert.equal(sourceRouting.status,2,sourceRouting.stderr+sourceRouting.stdout);
  const sourceJob=JSON.parse(fs.readFileSync(taskFile(sourceFixture),'utf8'));assert.equal(sourceJob.phase,'source_selection');fs.unlinkSync(taskFile(sourceFixture));
  console.log('PASS: a prompt-fixed 3CA study advances from one catalog call to exact get_study routing.');
  const literatureFixture=path.join(fixture,'research-literature-routing');
  for(const directory of ['inputs','results/core_analysis','sources/literature'])fs.mkdirSync(path.join(literatureFixture,directory),{recursive:true});
  fs.writeFileSync(path.join(literatureFixture,'inputs','staging_manifest.json'),'{}');fs.writeFileSync(path.join(literatureFixture,'results','core_analysis','core_result.json'),'{}');
  fs.writeFileSync(path.join(literatureFixture,'sources','literature','dataset.json'),JSON.stringify({requested_identifier:'3ca:20773',doi:'10.1038/s41588-022-01061-8'}));
  const literatureRouting=spawnSync(process.execPath,['--input-type=module','-e',`
    import assert from 'node:assert/strict';
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(literatureFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','1','--require-artifact','results/core_analysis/core_result.json','--require-artifact','results/analysis_manifest.json','use 3ca:20773 and cite 10.1038/s41586-023-06130-4'];
    globalThis.fetch=async(_url,options)=>{const body=JSON.parse(options.body);const runtime=JSON.parse(body.messages[0].content.split('Current authoritative engine runtime state:\\n')[1]);assert.equal(runtime.phase,'literature_verification');assert(runtime.next_required_action.includes('10.1038/s41586-023-06130-4'));assert(body.tools.map(item=>item.function.name).includes('verify_doi'));assert(body.tools.map(item=>item.function.name).includes('read_file'));assert(body.tools.map(item=>item.function.name).includes('run_powershell'));assert(!body.tools.map(item=>item.function.name).includes('build_research_report'));return {ok:true,json:async()=>({choices:[{message:{role:'assistant',content:'LITERATURE_ROUTING_CHECKED'}}]})};};
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:15000});
  assert.equal(literatureRouting.status,2,literatureRouting.stderr+literatureRouting.stdout);fs.unlinkSync(taskFile(literatureFixture));
  console.log('PASS: every DOI explicitly required by the research prompt is verified before report authoring.');
  const buildRepairFixture=path.join(fixture,'research-build-repair');
  for(const directory of ['inputs','results/core_analysis','sources/literature','report'])fs.mkdirSync(path.join(buildRepairFixture,directory),{recursive:true});
  for(const file of ['inputs/staging_manifest.json','results/core_analysis/core_result.json','sources/literature/verified.json','results/analysis_manifest.json'])fs.writeFileSync(path.join(buildRepairFixture,file),'{}');
  fs.writeFileSync(path.join(buildRepairFixture,'sources','literature','verified.json'),JSON.stringify({doi:'10.1/fixture'}));
  fs.writeFileSync(path.join(buildRepairFixture,'README.md'),'ready');
  fs.writeFileSync(path.join(buildRepairFixture,'report','main.tex'),'\\documentclass{article}\\begin{document}max_value\\end{document}');
  const buildRepair=spawnSync(process.execPath,['--input-type=module','-e',`
    import assert from 'node:assert/strict';
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(buildRepairFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','2','--require-artifact','results/core_analysis/core_result.json','--require-artifact','results/analysis_manifest.json','--require-artifact','report/main.tex','--require-artifact','report/main.pdf','--require-artifact','README.md','build repair probe'];
    let round=0;globalThis.fetch=async(_url,options)=>{const body=JSON.parse(options.body);round++;const runtime=JSON.parse(body.messages[0].content.split('Current authoritative engine runtime state:\\n')[1]);
      if(round===1){assert.equal(runtime.phase,'report_build');assert(body.tools.map(item=>item.function.name).includes('build_research_report'));assert(body.tools.map(item=>item.function.name).includes('read_file'));assert(body.tools.map(item=>item.function.name).includes('run_powershell'));return {ok:true,json:async()=>({choices:[{message:{role:'assistant',content:null,tool_calls:[{id:'repair-1',type:'function',function:{name:'build_research_report',arguments:'{}'}}]}}]})};}
      assert.equal(runtime.phase,'report_repair');assert.match(runtime.next_required_action,/Missing \\$ inserted/);assert(body.tools.some(item=>item.function.name==='replace_in_file'));assert(!body.tools.some(item=>item.function.name==='build_research_report'));return {ok:true,json:async()=>({choices:[{message:{role:'assistant',content:'BUILD_REPAIR_ROUTED'}}]})};};
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:20000});
  assert.equal(buildRepair.status,2,buildRepair.stderr+buildRepair.stdout);const buildRepairJob=JSON.parse(fs.readFileSync(taskFile(buildRepairFixture),'utf8'));assert.equal(buildRepairJob.phase,'report_repair');fs.unlinkSync(taskFile(buildRepairFixture));
  console.log('PASS: a native build failure routes to file repair before another compile attempt.');
  const buildCycleFixture=path.join(fixture,'research-build-cycle-stop');
  for(const directory of ['inputs','results/core_analysis','sources/literature','report'])fs.mkdirSync(path.join(buildCycleFixture,directory),{recursive:true});
  for(const [file,content] of [['inputs/staging_manifest.json','{}'],['results/core_analysis/core_result.json','{}'],['sources/literature/verified.json',JSON.stringify({doi:'10.1/fixture'})],['results/analysis_manifest.json','{}'],['README.md','ready']])fs.writeFileSync(path.join(buildCycleFixture,file),content);
  fs.writeFileSync(path.join(buildCycleFixture,'report','main.tex'),'\\documentclass{article}\\begin{document}bad_value\\end{document}');
  const buildCycle=spawnSync(process.execPath,['--input-type=module','-e',`
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(buildCycleFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','0','--require-artifact','results/core_analysis/core_result.json','--require-artifact','results/analysis_manifest.json','--require-artifact','report/main.tex','--require-artifact','report/main.pdf','--require-artifact','README.md','build cycle stop probe'];
    let round=0;const call=(name,args)=>({role:'assistant',content:null,tool_calls:[{id:'cycle-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    globalThis.fetch=async(_url,options)=>{const body=JSON.parse(options.body);round++;if(round>24)throw new Error('Build cycle did not stop after twelve native failures');const runtime=JSON.parse(body.messages[0].content.split('Current authoritative engine runtime state:\\n')[1]);const reply=runtime.phase==='report_build'?call('build_research_report',{}):call('write_file',{path:'report/main.tex',content:'\\\\documentclass{article}\\\\begin{document}bad_value '+round+'\\\\end{document}'});return {ok:true,json:async()=>({choices:[{message:reply}]})};};
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:60000});
  assert.equal(buildCycle.status,1,buildCycle.stderr+buildCycle.stdout);const buildCycleJobPath=taskFile(buildCycleFixture);const buildCycleJob=JSON.parse(fs.readFileSync(buildCycleJobPath,'utf8'));assert.equal(buildCycleJob.status,'needs_attention');assert.equal(buildCycleJob.stage_failures.build_research_report,12);fs.unlinkSync(buildCycleJobPath);
  console.log('PASS: twelve consecutive identical native build failures stop a report edit cycle even when the TeX file keeps changing.');
  const validationCycleFixture=path.join(fixture,'research-validation-cycle-stop');
  for(const directory of ['inputs','results/core_analysis','sources/literature','report'])fs.mkdirSync(path.join(validationCycleFixture,directory),{recursive:true});
  for(const [file,content] of [['inputs/staging_manifest.json','{}'],['results/core_analysis/core_result.json','{}'],['sources/literature/verified.json',JSON.stringify({doi:'10.1/fixture'})],['results/analysis_manifest.json','{}'],['report/main.tex','\\begin{document}report\\end{document}'],['README.md','ready']])fs.writeFileSync(path.join(validationCycleFixture,file),content);
  fs.writeFileSync(path.join(validationCycleFixture,'report','main.pdf'),'%PDF-'+('x'.repeat(1500)));
  const validationCycle=spawnSync(process.execPath,['--input-type=module','-e',`
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(validationCycleFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','0','--require-artifact','results/core_analysis/core_result.json','--require-artifact','results/analysis_manifest.json','--require-artifact','report/main.tex','--require-artifact','report/main.pdf','--require-artifact','README.md','validation cycle stop probe'];
    let round=0;const call=(name,args)=>({role:'assistant',content:null,tool_calls:[{id:'validation-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    globalThis.fetch=async(_url,options)=>{const body=JSON.parse(options.body);round++;if(round>24)throw new Error('Validation cycle did not stop after twelve failures');const runtime=JSON.parse(body.messages[0].content.split('Current authoritative engine runtime state:\\n')[1]);const reply=runtime.phase==='bundle_validation'?call('validate_research_bundle',{}):call('write_file',{path:'results/analysis_manifest.json',content:JSON.stringify({round})});return {ok:true,json:async()=>({choices:[{message:reply}]})};};
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:60000});
  assert.equal(validationCycle.status,1,validationCycle.stderr+validationCycle.stdout);const validationCycleJobPath=taskFile(validationCycleFixture);const validationCycleJob=JSON.parse(fs.readFileSync(validationCycleJobPath,'utf8'));assert.equal(validationCycleJob.status,'needs_attention');assert.equal(validationCycleJob.stage_failures.validate_research_bundle,12);fs.unlinkSync(validationCycleJobPath);
  console.log('PASS: twelve consecutive identical invalid bundle validations stop a manifest repair cycle even when the manifest keeps changing.');
  const validationProgressFixture=path.join(fixture,'research-validation-progress-reset');
  for(const directory of ['inputs','results/core_analysis','sources/literature','report'])fs.mkdirSync(path.join(validationProgressFixture,directory),{recursive:true});
  for(const [file,content] of [['inputs/staging_manifest.json','{}'],['results/core_analysis/core_result.json','{}'],['sources/literature/verified.json',JSON.stringify({doi:'10.1/fixture'})],['results/analysis_manifest.json','{}'],['report/main.tex','\\begin{document}report\\end{document}'],['README.md','ready']])fs.writeFileSync(path.join(validationProgressFixture,file),content);
  fs.writeFileSync(path.join(validationProgressFixture,'report','main.pdf'),'%PDF-'+('x'.repeat(1500)));
  const validationProgressPrompt='validation progress reset probe';
  const validationProgressJobPath=taskFile(validationProgressFixture);
  fs.writeFileSync(validationProgressJobPath,JSON.stringify({model:'Qwen3.5-4B',workspace:validationProgressFixture,prompt:validationProgressPrompt,required_artifacts:['results/core_analysis/core_result.json','results/analysis_manifest.json','report/main.tex','report/main.pdf','README.md'],phase:'bundle_validation',next_action:'validate',artifacts:[],evidence:[],observations:[],catalog_references:[],rounds:0,status:'interrupted',workspace_version:0,messages:[{role:'system',content:'old'}],stage_failures:{validate_research_bundle:11},stage_failure_signatures:{validate_research_bundle:'an-earlier-error-set'}}));
  const validationProgress=spawnSync(process.execPath,['--input-type=module','-e',`
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(validationProgressFixture)},'--allow-write','--allow-shell','--autonomous','--resume','--max-rounds','1','--require-artifact','results/core_analysis/core_result.json','--require-artifact','results/analysis_manifest.json','--require-artifact','report/main.tex','--require-artifact','report/main.pdf','--require-artifact','README.md',${JSON.stringify(validationProgressPrompt)}];
    globalThis.fetch=async()=>({ok:true,json:async()=>({choices:[{message:{role:'assistant',content:null,tool_calls:[{id:'progress-reset',type:'function',function:{name:'validate_research_bundle',arguments:'{}'}}]}}]})});
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:30000});
  assert.equal(validationProgress.status,2,validationProgress.stderr+validationProgress.stdout);const validationProgressJob=JSON.parse(fs.readFileSync(validationProgressJobPath,'utf8'));assert.equal(validationProgressJob.status,'budget_exhausted');assert.equal(validationProgressJob.stage_failures.validate_research_bundle,1);fs.unlinkSync(validationProgressJobPath);
  console.log('PASS: a changed validator error set resets the consecutive-failure counter instead of terminating a progressing repair.');
  const bundleRepairFixture=path.join(fixture,'research-bundle-repair-paths');
  for(const directory of ['inputs','results/core_analysis','sources/literature','report'])fs.mkdirSync(path.join(bundleRepairFixture,directory),{recursive:true});
  for(const [file,content] of [['inputs/staging_manifest.json','{}'],['results/core_analysis/core_result.json','{}'],['sources/literature/verified.json',JSON.stringify({doi:'10.1/fixture'})],['results/analysis_manifest.json','{}'],['report/main.tex','\\begin{document}report\\end{document}'],['README.md','ready']])fs.writeFileSync(path.join(bundleRepairFixture,file),content);
  fs.writeFileSync(path.join(bundleRepairFixture,'report','main.pdf'),'%PDF-'+('x'.repeat(1500)));
  const bundleRepair=spawnSync(process.execPath,['--input-type=module','-e',`
    import assert from 'node:assert/strict';
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(bundleRepairFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','2','--require-artifact','results/core_analysis/core_result.json','--require-artifact','results/analysis_manifest.json','--require-artifact','report/main.tex','--require-artifact','report/main.pdf','--require-artifact','README.md','bundle repair path probe'];
    let round=0;const call=(name,args)=>({role:'assistant',content:null,tool_calls:[{id:'bundle-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    globalThis.fetch=async(_url,options)=>{const body=JSON.parse(options.body);round++;const runtime=JSON.parse(body.messages[0].content.split('Current authoritative engine runtime state:\\n')[1]);
      if(round===1){assert.equal(runtime.phase,'bundle_validation');return {ok:true,json:async()=>({choices:[{message:call('validate_research_bundle',{})}]})};}
      assert.equal(runtime.phase,'bundle_repair');assert(body.tools.some(item=>item.function.name==='write_file'));return {ok:true,json:async()=>({choices:[{message:call('write_file',{path:'temp_read.txt',content:'irrelevant mutation'})}]})};};
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:30000});
  assert.equal(bundleRepair.status,2,bundleRepair.stderr+bundleRepair.stdout);assert(!fs.existsSync(path.join(bundleRepairFixture,'temp_read.txt')));const bundleRepairJob=JSON.parse(fs.readFileSync(taskFile(bundleRepairFixture),'utf8'));assert.equal(bundleRepairJob.workspace_version,0);fs.unlinkSync(taskFile(bundleRepairFixture));
  console.log('PASS: research repair phases reject writes outside the exact failing deliverables.');
  const jobPath = taskFile(autonomousFixture);
  const job = JSON.parse(fs.readFileSync(jobPath, "utf8"));
  assert.equal(job.status, "completed_candidate");
  const events = fs.readFileSync(job.session_file, "utf8").trim().split("\n").map(JSON.parse);
  const reasoning = events.find((event) => event.payload.type === "reasoning");
  assert.equal(reasoning.payload.content[0].text, "LOCAL_RETURNED_REASONING_FIXTURE");
  assert.equal(reasoning.payload.workflow.raw_fields.reasoning_content, "LOCAL_RETURNED_REASONING_FIXTURE");
  assert.deepEqual(reasoning.payload.summary, []);
  assert(events.some((event) => event.payload.workflow?.event === "model_response"));
  const resumed = spawnSync(process.execPath, [fileURLToPath(new URL("./wingpt.js", import.meta.url)), "--workspace", autonomousFixture, "--autonomous", "--allow-write", "--allow-shell", "--resume"], { encoding: "utf8", timeout: 10000 });
  assert.equal(resumed.status, 0, resumed.stderr);
  assert.match(resumed.stdout, /not rerunning mutations/);
  job.status = "interrupted";
  job.messages.push({role:"assistant",content:null,tool_calls:[{id:"unknown-mutation",type:"function",function:{name:"append_file",arguments:JSON.stringify({path:"nested/result.txt",content:"DUPLICATE"})}}]});
  fs.writeFileSync(jobPath, JSON.stringify(job), "utf8");
  const interrupted = spawnSync(process.execPath, ["--input-type=module", "-e", `
    import assert from 'node:assert/strict';
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(autonomousFixture)},'--autonomous','--resume','--allow-write','--allow-shell'];
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
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(budgetFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','1','unfinished probe'];
    globalThis.fetch=async()=>({ok:true,json:async()=>({choices:[{message:{role:'assistant',content:'A plan, not an artifact'}}]})});
    await import(${JSON.stringify(entry)});
  `], {encoding:"utf8",timeout:15000});
  assert.equal(budget.status, 2, budget.stderr);
  const budgetJobPath = taskFile(budgetFixture);
  assert.equal(JSON.parse(fs.readFileSync(budgetJobPath,"utf8")).status,"budget_exhausted"); fs.unlinkSync(budgetJobPath);
  const untilFixture = path.join(fixture, "until-complete"); fs.mkdirSync(untilFixture);
  const untilComplete = spawnSync(process.execPath, ["--input-type=module", "-e", `
    import assert from 'node:assert/strict';
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(untilFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','0','--require-artifact','done.txt','until complete probe'];
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
  const persistentStallFixture=path.join(fixture,'persistent-stall');fs.mkdirSync(persistentStallFixture);
  fs.writeFileSync(path.join(persistentStallFixture,'evidence.txt'),Array.from({length:40},(_,index)=>`line ${index+1}`).join('\n'));
  const persistentStall=spawnSync(process.execPath,['--input-type=module','-e',`
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(persistentStallFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','0','--require-artifact','done.txt','persistent stall probe'];
    let round=0;globalThis.fetch=async()=>{round++;if(round>160)throw new Error('Engine did not stop after twelve identical recoveries');return {ok:true,json:async()=>({choices:[{message:{role:'assistant',content:null,tool_calls:[{id:'stall-'+round,type:'function',function:{name:'read_file',arguments:JSON.stringify({path:'evidence.txt',start_line:round,end_line:round})}}]}}]})};};
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:120000});
  assert.equal(persistentStall.status,1,persistentStall.stderr+persistentStall.stdout);
  const persistentStallJobPath=taskFile(persistentStallFixture);assert(fs.existsSync(persistentStallJobPath),persistentStall.stderr+persistentStall.stdout);const persistentStallJob=JSON.parse(fs.readFileSync(persistentStallJobPath,'utf8'));
  assert.equal(persistentStallJob.status,'needs_attention');assert.equal(persistentStallJob.recovery_streak,12);assert.match(persistentStallJob.last_error,/12 recoveries/);
  fs.unlinkSync(persistentStallJobPath);
  console.log('PASS: max-rounds 0 stops after twelve recoveries of the same phase and workspace version.');
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
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(explorationFixture)},'--autonomous','--allow-write','--allow-shell','--max-rounds','0','--require-artifact','done.txt','Build a text artifact at C:/Users/User/Desktop/agentic/task'];
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
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(pathOnlyFixture)},'--autonomous','--allow-write','--allow-shell','--require-artifact','done.txt','path-only shell probe'];
    let round=0;
    const call=(name,args)=>({role:'assistant',content:null,tool_calls:[{id:'path-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    globalThis.fetch=async(_url,options)=>{
      const body=JSON.parse(options.body);round++;
      if(round===2){assert(body.messages.at(-1).content.includes('filesystem path alone'));assert(body.tools.some(tool=>tool.function.name==='run_powershell'));}
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
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(catalogFixture)},'--autonomous','--allow-write','--allow-shell','--require-artifact','done.txt','catalog loop probe'];
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
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(formatFixture)},'--autonomous','--allow-write','--allow-shell','format validation probe'];
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
  const qualityFixture=path.join(fixture,'research-quality-hook');fs.mkdirSync(qualityFixture);
  const quality=spawnSync(process.execPath,['--input-type=module','-e',`
    import assert from 'node:assert/strict';
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(qualityFixture)},'--autonomous','--allow-write','--allow-shell','--require-artifact','done.txt','research quality hook probe'];
    let round=0;const call=(name,args)=>({role:'assistant',content:null,tool_calls:[{id:'quality-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    globalThis.fetch=async(_url,options)=>{const body=JSON.parse(options.body);round++;
      const replies=[
        call('write_file',{path:'done.txt',content:'QUALITY_OK'}),
        call('write_file',{path:'results/analysis_manifest.json',content:'{"schema_version":1}'}),
        call('run_powershell',{command:'Write-Output QUALITY_VALIDATED'}),
        call('complete_task',{artifacts:['done.txt','results/analysis_manifest.json'],verification_call_id:'quality-3',summary:'invalid manifest'}),
        call('read_file',{path:'done.txt'}),
        call('complete_task',{artifacts:['done.txt'],verification_call_id:'quality-3',summary:'QUALITY_HOOK_OK'})
      ];
      return {ok:true,json:async()=>({choices:[{message:replies[round-1]}]})};};
    await import(${JSON.stringify(entry)});
  `],{encoding:'utf8',timeout:20000});
  assert.equal(quality.status,0,`${quality.stderr}\n${quality.stdout}`);assert.match(quality.stdout,/dataset\.study_id is required/);assert.match(quality.stdout,/QUALITY_HOOK_OK/);fs.unlinkSync(taskFile(qualityFixture));
  console.log('PASS: complete_task rejects a structurally nonempty but scientifically incomplete analysis manifest.');
  const rerunFixture = path.join(fixture, 'research-rerun');
  fs.mkdirSync(rerunFixture);
  const rerun = spawnSync(process.execPath, ['--input-type=module', '-e', `
    import assert from 'node:assert/strict';
    process.argv = ['node', 'wingpt.js', '--workspace', ${JSON.stringify(rerunFixture)}, '--allow-write', '--max-rounds', '20', 'Check research reruns after file edits'];
    let round = 0;
    const call = (name,args) => ({role:'assistant',content:null,tool_calls:[{id:'rerun-'+round,type:'function',function:{name,arguments:JSON.stringify(args)}}]});
    const analysis = {expression_path:'counts.mtx',cells_path:'cells.csv',genes_path:'genes.txt',metabolic_genes_path:'metabolic.txt'};
    globalThis.fetch = async (_url, options) => {
      const body = JSON.parse(options.body); round++;
      const payload = () => JSON.parse(body.messages.at(-1).content.replace(/^ERROR: /,''));
      if (round===3) assert(payload().errors.includes('schema_version must be 1'));
      if (round===5) assert(!payload().errors.includes('schema_version must be 1'), 'Bundle validation must recompute after mutation');
      if (round===7) assert.equal(payload().valid,false);
      if (round===9) assert.equal(payload().valid,true, 'Code audit must recompute after mutation');
      if (round===10) assert.match(body.messages.at(-1).content,/expression path/);
      if (round===12) assert.match(body.messages.at(-1).content,/cells path/, 'Core rerun must execute again after inputs change, not reuse its old error');
      const replies = [
        call('write_file',{path:'manifest.json',content:'{"schema_version":0}'}),
        call('validate_research_bundle',{manifest_path:'manifest.json'}),
        call('write_file',{path:'manifest.json',content:'{"schema_version":1}'}),
        call('validate_research_bundle',{manifest_path:'manifest.json'}),
        call('write_file',{path:'analysis.py',content:'print(missing_name)'}),
        call('audit_analysis_code',{path:'analysis.py'}),
        call('write_file',{path:'analysis.py',content:'print(1)'}),
        call('audit_analysis_code',{path:'analysis.py'}),
        call('analyze_metabolic_states',analysis),
        call('write_file',{path:'counts.mtx',content:'input-presence engineering probe'}),
        call('analyze_metabolic_states',analysis),
        {role:'assistant',content:'RERUN_CHECK_OK'}
      ];
      assert(round<=replies.length);
      return {ok:true,json:async()=>({choices:[{message:replies[round-1]}]})};
    };
    await import(${JSON.stringify(entry)});
  `], {encoding:'utf8',timeout:60000});
  assert.equal(rerun.status,0,rerun.stderr+rerun.stdout);
  assert.match(rerun.stdout,/RERUN_CHECK_OK/);
  console.log('PASS: bundle/code checks and core-analysis retries recompute on changed workspace inputs; unchanged duplicate guards remain intact.');
  const structuredFixture = path.join(fixture, 'truncated-action-recovery'); fs.mkdirSync(structuredFixture);
  const structured = spawnSync(process.execPath, ['--input-type=module','-e',`
    import assert from 'node:assert/strict';
    import fs from 'node:fs';
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(structuredFixture)},'--allow-write','--allow-shell','--autonomous','--max-rounds','0','--require-artifact','done.txt','structured engineering probe'];
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
    process.argv=['node','wingpt.js','--workspace',${JSON.stringify(staleFixture)},'--autonomous','--allow-write','--allow-shell','--resume'];
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
  const actualLauncherSource=fs.readFileSync(fileURLToPath(new URL('../../run-wingpt.ps1',import.meta.url)),'utf8');
  assert.ok(actualLauncherSource.includes('.runtime\\node-v24.21.0-win-x64\\node.exe'),'Windows agent launcher must use the fixed project-local Node runtime');
  assert.match(actualLauncherSource,/& \$nodePath --no-maglev .*codex\.js/,'Windows agent launcher must disable the crashing Maglev tier');
  const launcherSource=actualLauncherSource
    .replace(/\$expectedRoot = '[^']*'/,"$expectedRoot = '"+launcherFixture.replaceAll("'","''")+"'")
    .replaceAll("& (Join-Path $PSScriptRoot 'start-wingpt-server.ps1')",'Write-Output MOCK_SERVER_READY')
    .replace(/& \$nodePath --no-maglev \(Join-Path \$PSScriptRoot 'codex-cli\\bin\\codex.js'\) --allow-network @taskArguments/,
      "if ($attempt -eq 1) { $global:LASTEXITCODE = 75 } else { if ($taskArguments -notcontains '--resume') { throw 'Missing --resume' }; $global:LASTEXITCODE = 0 }");
  const launcherScript=path.join(launcherFixture,'run-wingpt.ps1'); fs.writeFileSync(launcherScript,launcherSource);
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
