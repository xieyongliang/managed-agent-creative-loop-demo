// Packages the Skill, uploads it and creates the Managed Agent that runs it. Prints the IDs to put into .env.
import {mkdir,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';

process.chdir(fileURLToPath(new URL('.',import.meta.url)));
const [model,name='pod-creative-studio']=process.argv.slice(2);
if(!model){
 console.error('Usage: node deploy-agent.mjs <MA_MODEL_ID> [agent-name]\nList the models your account can use with: arkcli agent model list --format json\nSet SKILL_ID to publish a new version of an existing Skill instead of creating one.');
 process.exit(1);
}
const run=promisify(execFile),env={...process.env,ARKCLI_NO_UPDATE_NOTIFIER:'1',ARKCLI_CALLER_TYPE:'ai_agent',ARKCLI_CALLER_NAME:'pod-creative-studio',ARKCLI_SKILL_NAME:'arkcli-agent'};
async function cli(args){
 const call=run('arkcli',[...args,'--format','json'],{timeout:180000,maxBuffer:8e6,env});call.child.stdin.end();
 const x=JSON.parse((await call).stdout);if(x.ok===false)throw Error(x.error?.message||'ArkCLI failed');return x;
}
// Responses differ between CLI versions, so the first matching field is used and anything else stops the script.
const pick=(x,...keys)=>{for(const k of keys)for(const o of [x.Result,x.result,x.data,x])if(o&&o[k]!==undefined&&o[k]!==null)return o[k];};

await mkdir('data',{recursive:true});await rm('data/pod-creative-loop.zip',{force:true});
await run('zip',['-r','-q','../data/pod-creative-loop.zip','pod-creative-loop','-x','*/__pycache__/*','*.pyc'],{cwd:'skills'});
const skill=await cli(process.env.SKILL_ID?['agent','skill','update',process.env.SKILL_ID,'--zip','data/pod-creative-loop.zip']:['agent','skill','create','--zip','data/pod-creative-loop.zip','--display-title','POD Creative Loop']);
const skillId=process.env.SKILL_ID||pick(skill,'SkillId','skill_id','Id','id'),version=pick(skill,'Version','version','LatestVersion','latest_version');
if(!skillId||version===undefined){console.error('The Skill was uploaded but its ID or version could not be read. Response:\n'+JSON.stringify(skill,null,2)+'\nCreate the Agent by hand as described in the README.');process.exit(1);}
const agent=await cli(['agent','agent','create','--name',name,'--model',model,'--system','@cloud-system.md','--skill',JSON.stringify({SkillId:skillId,Version:String(version)})]);
const agentId=pick(agent,'AgentId','agent_id','Id','id');
if(!agentId){console.error('The Agent could not be confirmed. Response:\n'+JSON.stringify(agent,null,2));process.exit(1);}
console.log(JSON.stringify({skill_id:skillId,skill_version:version,agent_id:agentId,model},null,2));
console.log(`\nPut this into .env:\nCLOUD_AGENT_ID=${agentId}\nThen check the binding: arkcli agent agent get ${agentId} --format json --transform 'Result.Skills'`);
