// Creates the Cloud Environment and injects a user-approved demo key without logging it or putting it in argv.
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
if(!process.env.ARK_API_KEY)throw Error('Provide ARK_API_KEY through the process environment');
const name=process.env.CLOUD_ENVIRONMENT_NAME||'pod-creative-studio-'+new Date().toISOString().slice(0,10).replaceAll('-','');
// Model names are not secrets; they let one deployment use different generation or review models.
const models=Object.fromEntries(['IMAGE_MODEL','VIDEO_MODEL','EVAL_MODEL'].filter(k=>process.env[k]).map(k=>[k,process.env[k]]));
const dir=await mkdtemp(join(tmpdir(),'pod-studio-env-'));
try{
 const path=join(dir,'config.json');
 await writeFile(path,JSON.stringify({Type:'cloud',Networking:{Type:'unrestricted'},Env:{ARK_API_KEY:process.env.ARK_API_KEY,...models}}),{mode:0o600});
 const call=promisify(execFile)('arkcli',['agent','env','create','--name',name,'--config','@'+path,'--format','json'],{timeout:90000,maxBuffer:2000000,env:{...process.env,ARKCLI_NO_UPDATE_NOTIFIER:'1',ARKCLI_CALLER_TYPE:'ai_agent',ARKCLI_CALLER_NAME:'pod-creative-studio',ARKCLI_SKILL_NAME:'arkcli-agent'}});
 call.child.stdin.end();
 const {stdout}=await call;const result=JSON.parse(stdout);const id=result.Result?.Id||result.id;
 if(!id)throw Error('Environment not confirmed; inspect account before retrying');
 console.log(JSON.stringify({environment_id:id,name,models:Object.keys(models),credential:'injected; value withheld'}));
}catch{console.error('Environment creation not confirmed; response withheld to protect credentials. Inspect account before retrying.');process.exitCode=1;}
finally{await rm(dir,{recursive:true,force:true});}
