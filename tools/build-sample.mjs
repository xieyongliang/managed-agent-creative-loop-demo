// Rebuilds public/sample/campaign.json by passing the sample content through the real helper and the real bridge.
import {execFileSync} from 'node:child_process';
import {writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {validateBrief} from '../core.mjs';
import {cloudLimits,runPhase} from '../cloud.mjs';

process.chdir(fileURLToPath(new URL('..',import.meta.url)));
Object.assign(process.env,{CLOUD_AGENT_ID:'agent-sample',CLOUD_ENVIRONMENT_ID:'env-sample',REHEARSAL:'true'});
const made=JSON.parse(execFileSync('python3',['tools/sample/build.py'],{encoding:'utf8',maxBuffer:64e6}));
const job={id:'00000000-0000-4000-8000-000000000000',brief:validateBrief(made.brief),limits:cloudLimits(made.limits),mode:'ma_cloud',stage:'draft',busy:false};

// The recorded events are replayed as the Session history; the bridge validates them exactly as it would a live run.
const history=[];
for(const phase of ['explore','produce']){
 if(phase==='produce'){job.selection=made.selection;job.stage='producing';}
 const cli=async args=>{
  if(args[2]==='create')return {id:'sample-session'};
  if(args[3]==='list')return {data:[...history]};
  const message={id:'msg-'+history.length,type:'user.message',created_at:made[phase][0].created_at,content:[{type:'text',text:args[args.indexOf('--text')+1]}]};
  history.push(message,...made[phase].map((e,i)=>({id:`${phase}-${i}`,...e})));return {data:[message]};
 };
 await runPhase(job,phase,{cli,save:async()=>{},pause:async()=>{},interval:0,today:'2026-09-30'});
 if(job.error)throw Error(phase+': '+job.error);
 Object.assign(job.cloud[phase],{started:made[phase][0].created_at,finished:made[phase].at(-1).created_at});
 for(const key of ['sent','final_text','first','sendStarted'])delete job.cloud[phase][key];
}
delete job.cloud.createStarted;
Object.assign(job,{created:'2026-09-30T02:04:00.000Z',sample:true,
 sample_note:'The market sources are real pages and public catalogs read on 30 Sep 2026. Images and videos are stand-ins, partly from an earlier real run, and the reviewer comments are written examples.'});
await writeFile('public/sample/campaign.json',JSON.stringify(job,null,1)+'\n');
console.log(`Sample written: ${job.explore.variants.length} designs, ${job.final.variants.length} produced, winner ${job.final.winner}, ${JSON.stringify(job).length} bytes`);
