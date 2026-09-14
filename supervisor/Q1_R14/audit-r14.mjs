import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root=path.dirname(fileURLToPath(import.meta.url));
const workflow="C:\\Users\\User\\Desktop\\agentic\\workflow_codex",task="C:\\Users\\User\\Desktop\\agentic\\3CA\\Q1_R14";
const home=path.join(workflow,".runtime","codex-home"),jobFile=path.join(home,"tasks",createHash("sha256").update(task.toLowerCase()).digest("hex").slice(0,24)+".json");
const readJson=file=>JSON.parse(fs.readFileSync(file,"utf8").replace(/^\uFEFF/,""));
const walk=directory=>!fs.existsSync(directory)?[]:fs.readdirSync(directory,{withFileTypes:true}).flatMap(item=>item.isDirectory()?walk(path.join(directory,item.name)):item.isFile()?[path.join(directory,item.name)]:[]);
const manifest=fs.existsSync(path.join(root,"run-manifest.json"))?readJson(path.join(root,"run-manifest.json")):null;
const runner=fs.existsSync(path.join(root,"runner-result.json"))?readJson(path.join(root,"runner-result.json")):null;
let job=null,checkpoint_error=null;try{if(fs.existsSync(jobFile))job=readJson(jobFile);}catch(error){checkpoint_error=error.message;}
const sessions=[],tools={},failures=[];
for(const file of walk(path.join(home,"sessions")).filter(file=>file.endsWith(".jsonl"))){
  const events=[];for(const line of fs.readFileSync(file,"utf8").trimEnd().split("\n"))try{events.push(JSON.parse(line));}catch{}
  const metadata=events.find(event=>event.type==="session_meta");if(!metadata||metadata.payload?.cwd!==task||Date.parse(metadata.timestamp)<Date.parse(manifest?.started_at||0))continue;
  for(const event of events){const data=event.payload||{},meta=data.workflow||{};if(meta.event==="tool_result"){tools[meta.name]=(tools[meta.name]||0)+1;if(String(meta.result).startsWith("ERROR:"))failures.push({session:path.basename(file),tool:meta.name,result:String(meta.result).slice(0,2000)});}}
  sessions.push({file,events:events.length,bytes:fs.statSync(file).size});
}
let alive=false;if(manifest?.runner_pid)try{process.kill(manifest.runner_pid,0);alive=true;}catch{}
const required=["report/main.tex","report/main.pdf","results/summary.json","results/analysis_manifest.json","README.md"].map(file=>({file,present:fs.existsSync(path.join(task,file))&&fs.statSync(path.join(task,file)).size>0}));
let research_validation=null;
if(fs.existsSync(path.join(task,"results","analysis_manifest.json"))){
  const python=path.join(workflow,"tools","tool43CA",".venv","Scripts","python.exe"),cli=path.join(workflow,"tools","research-quality","research_quality.py");
  const checked=spawnSync(python,[cli,"--workspace",task,"validate"],{encoding:"utf8",timeout:0,maxBuffer:64*1024*1024});
  try{research_validation=JSON.parse(checked.stdout);}catch{research_validation={valid:false,error:checked.stderr||checked.stdout};}
}
const frozen_mismatches=(manifest?.frozen_files||[]).filter(item=>!fs.existsSync(path.join(workflow,item.file))||createHash("sha256").update(fs.readFileSync(path.join(workflow,item.file))).digest("hex")!==item.sha256).map(item=>item.file);
const audit={snapshot_at:new Date().toISOString(),status:runner?.runner_success===false?"runner_failed":runner?.runner_success===true?"runner_finished":job?.status||"not_started",runner_alive:alive,checkpoint_error,rounds:job?.rounds,phase:job?.phase,next_action:job?.next_action,tools,failures,required_artifacts:required,research_validation,frozen_mismatches,structural_completion_candidate:runner?.runner_success===true&&job?.status==="completed_candidate"&&required.every(item=>item.present)&&research_validation?.valid===true&&!frozen_mismatches.length,semantic_acceptance:"pending_independent_review"};
fs.writeFileSync(path.join(root,"audit.json"),JSON.stringify(audit,null,2),"utf8");
console.log(JSON.stringify(audit,null,2));
