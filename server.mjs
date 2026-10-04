import http from 'node:http';
import {readFile,writeFile,mkdir,rename,stat} from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {PRODUCTS,PLATFORMS,validateBrief} from './core.mjs';
import {LANGUAGES,cloudLimits,runPhase} from './cloud.mjs';
const root=fileURLToPath(new URL('.',import.meta.url));process.chdir(root);
const port=Number(process.env.PORT||8790), exec=promisify(execFile);
// Rehearsal mode swaps the cloud for a scripted agent that plays bundled sample results. No model is called.
const rehearsal=process.env.REHEARSAL==='true',sample=JSON.parse(await readFile('public/sample/campaign.json','utf8'));
const brand={name:(process.env.STUDIO_NAME||'POD Creative Studio').slice(0,40),workspace:(process.env.WORKSPACE_NAME||'Demo workspace').slice(0,40)};
const data=process.env.DATA_DIR||'data';
await mkdir(data,{recursive:true});
let jobs={};try{jobs=JSON.parse(await readFile(data+'/jobs.json','utf8'));}catch(e){if(e.code!=='ENOENT')throw e;}
// A saved sample always shows the content that ships with this version.
for(const [id,j] of Object.entries(jobs))if(j.sample)jobs[id]={...structuredClone(sample),id,sample:true,busy:false,created:j.created,...(j.archived?{archived:true}:{})};
for(const j of Object.values(jobs))if(j.busy){j.busy=false;j.error='The local observer restarted. Resume to keep watching the same Cloud Session; nothing is sent again.';}
let saveQueue=Promise.resolve();function save(){const snapshot=JSON.stringify(jobs,null,2);saveQueue=saveQueue.then(async()=>{await writeFile(data+'/jobs.tmp',snapshot,{mode:0o600});await rename(data+'/jobs.tmp',data+'/jobs.json');});return saveQueue;}
function safeError(e){return String(e.message||e).replace(/Bearer\s+\S+/gi,'Bearer [redacted]').replaceAll(process.env.ARK_API_KEY||'__no_key__','[redacted]').slice(0,1200);}
async function cli(args,timeout=120000){
  let stdout;
  try{const pending=exec(rehearsal?process.execPath:'arkcli',[...(rehearsal?['tools/rehearsal/arkcli.mjs']:[]),...args,'--format','json'],{timeout,maxBuffer:64e6,env:{...process.env,ARKCLI_NO_UPDATE_NOTIFIER:'1',ARKCLI_CALLER_TYPE:'ai_agent',ARKCLI_CALLER_NAME:'pod-creative-studio',ARKCLI_SKILL_NAME:'arkcli-agent'}});pending.child.stdin.end();({stdout}=await pending);}
  catch(e){let detail;try{detail=JSON.parse(e.stdout).error?.message;}catch{}throw Error(detail||e.stderr?.trim()||'ArkCLI failed or timed out; inspect the retained session.');}
  const x=JSON.parse(stdout);if(x.ok===false)throw Error(x.error?.message||'ArkCLI failed');return x;
}
const ready=()=>rehearsal||!!(process.env.CLOUD_AGENT_ID&&process.env.CLOUD_ENVIRONMENT_ID);
const live=()=>rehearsal||(ready()&&process.env.ENABLE_PAID_RUNS==='true');
const interval=Number(process.env.OBSERVE_INTERVAL_MS)||(rehearsal?1500:8000);
const phaseOf=j=>j.stage==='draft'||j.stage==='exploring'?'explore':j.stage==='producing'?'produce':null;
function summary(j){
 // Finished sample and rehearsal campaigns carry local media paths; everything else is a signed remote URL.
 const best=j.final?.variants.find(v=>v.id===j.final.winner),round=best?.rounds.find(r=>r.number===best.best_round);
 return {id:j.id,name:j.brief.name,product:j.brief.product,platform:j.brief.platform,stage:j.stage,busy:j.busy,failed:!!j.error,sample:!!j.sample,rehearsal:!!j.rehearsal,created:j.created,
  cover:round?.mockup?.url||j.explore?.variants.find(v=>v.design)?.design.url||null,score:round?.review?.score??null,met_target:j.final?.met_target??null};
}
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.jpg':'image/jpeg','.png':'image/png','.svg':'image/svg+xml','.webp':'image/webp','.mp4':'video/mp4'};
const pages={'/':'public/index.html','/app.js':'public/app.js','/style.css':'public/style.css','/icons.js':'node_modules/lucide/dist/umd/lucide.min.js'};
const policy="default-src 'self'; img-src 'self' https: data:; media-src 'self' https:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; frame-ancestors 'none'";
async function file(req,res,path){
 const type=types[path.slice(path.lastIndexOf('.'))]||'application/octet-stream',head={'Content-Type':type,'X-Content-Type-Options':'nosniff','Content-Security-Policy':policy};
 if(!type.startsWith('video/')){res.writeHead(200,{...head,'Cache-Control':path.startsWith('public/sample/')?'max-age=3600':'no-cache'});return res.end(await readFile(path));}
 // Browsers request video in byte ranges; without them seeking and Safari playback fail.
 const {size}=await stat(path),m=/^bytes=(\d*)-(\d*)$/.exec(req.headers.range||'');
 if(!m){res.writeHead(200,{...head,'Content-Length':size,'Accept-Ranges':'bytes'});return createReadStream(path).pipe(res);}
 const start=m[1]?Number(m[1]):Math.max(0,size-Number(m[2])),end=m[1]&&m[2]?Math.min(Number(m[2]),size-1):size-1;
 if(start>end||start>=size){res.writeHead(416,{'Content-Range':`bytes */${size}`});return res.end();}
 res.writeHead(206,{...head,'Content-Range':`bytes ${start}-${end}/${size}`,'Content-Length':end-start+1,'Accept-Ranges':'bytes'});createReadStream(path,{start,end}).pipe(res);
}
http.createServer(async(req,res)=>{const respond=(status,obj)=>{res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(obj));};try{
 const u=new URL(req.url,'http://localhost');if(!['127.0.0.1','localhost'].includes((req.headers.host||'').split(':')[0]))return respond(403,{error:'Local access only'});
 if(req.method==='POST'&&req.headers.origin&&!['http://127.0.0.1:'+port,'http://localhost:'+port].includes(req.headers.origin))return respond(403,{error:'Origin rejected'});
 if(u.pathname==='/api/status')return respond(200,{brand,rehearsal,configured:ready(),paid:process.env.ENABLE_PAID_RUNS==='true',live:live(),sample:{brief:sample.brief,limits:sample.limits},credentials:process.env.ARK_API_KEY?'server environment':'ArkCLI profile',
  options:{products:PRODUCTS,platforms:PLATFORMS,languages:LANGUAGES}});
 const one=u.pathname.match(/^\/api\/jobs\/([a-f0-9-]+)$/);
 if(req.method==='GET'){
  if(u.pathname==='/api/jobs')return respond(200,Object.values(jobs).filter(j=>!j.archived).reverse().map(summary));
  if(one)return jobs[one[1]]&&!jobs[one[1]].archived?respond(200,jobs[one[1]]):respond(404,{error:'Not found'});
 }
 if(req.method==='POST'){
  let buf='';for await(const chunk of req){buf+=chunk;if(buf.length>20000)return respond(413,{error:'Request too large'});}const body=JSON.parse(buf||'{}');
  if(u.pathname==='/api/jobs'){
   // The scripted agent can only play the sample campaign, so a rehearsal always uses its brief and settings.
   const brief=rehearsal?{...sample.brief,name:validateBrief({...sample.brief,name:body.name}).name}:validateBrief(body),limits=rehearsal?sample.limits:cloudLimits(body),id=randomUUID();
   jobs[id]={id,brief,limits,mode:'ma_cloud',stage:'draft',created:new Date().toISOString(),busy:false,...(rehearsal?{rehearsal:true}:{})};await save();return respond(201,jobs[id]);
  }
  if(u.pathname==='/api/sample'){
   const existing=Object.values(jobs).find(j=>j.sample&&!j.archived);if(existing)return respond(200,existing);
   const id=randomUUID();jobs[id]={...structuredClone(sample),id,sample:true,busy:false,created:new Date().toISOString()};await save();return respond(201,jobs[id]);
  }
  const m=u.pathname.match(/^\/api\/jobs\/([a-f0-9-]+)\/(start|select|archive)$/);if(!m||!jobs[m[1]]||jobs[m[1]].archived)return respond(404,{error:'Not found'});const j=jobs[m[1]];
  if(j.busy)return respond(409,{error:'This campaign is already running'});
  if(m[2]==='archive'){j.archived=true;await save();return respond(200,{archived:true});}
  if(j.sample)return respond(409,{error:'The sample campaign is a finished example. Create a campaign to run the agent.'});
  if(!!j.rehearsal!==rehearsal)return respond(409,{error:j.rehearsal?'This campaign was rehearsed with the simulated agent. Create a new campaign for a live run.':'Live campaigns cannot continue in rehearsal mode. Restart without REHEARSAL.'});
  if(!live())return respond(409,{error:'Live runs are not configured. Set CLOUD_AGENT_ID, CLOUD_ENVIRONMENT_ID and ENABLE_PAID_RUNS=true in .env, then restart.'});
  if(m[2]==='select'){
   const ids=body.selected,available=(j.explore?.variants||[]).filter(v=>v.design).map(v=>v.id);
   if(j.stage!=='choosing'||!Array.isArray(ids)||!ids.length||ids.length>j.limits.select_max||new Set(ids).size!==ids.length||ids.some(x=>!available.includes(x)))return respond(409,{error:`Choose 1 to ${j.limits.select_max} of the generated designs`});
   j.selection=ids;j.stage='producing';
  }
  const phase=phaseOf(j);if(!phase)return respond(409,{error:j.stage==='choosing'?'Choose the designs to continue':'This campaign has finished'});
  void runPhase(j,phase,{cli,save,interval});return respond(202,j);
 }
 const media=/^\/sample\/media\/[a-z0-9-]+\.(jpg|png|svg|webp|mp4)$/.test(u.pathname)?'public'+u.pathname:null;
 const path=pages[u.pathname]||media;if(!path)return respond(404,{error:'Not found'});
 await file(req,res,path);
 }catch(e){respond(e.code==='ENOENT'?404:400,{error:safeError(e)});}}).listen(port,'127.0.0.1',()=>console.log(`${brand.name} http://127.0.0.1:${port}`));
