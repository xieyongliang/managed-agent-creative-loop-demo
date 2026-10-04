// Runs the real server in rehearsal mode and walks a whole campaign through its HTTP interface.
import {test,before,after} from 'node:test';import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';import {mkdtemp,rm,readFile} from 'node:fs/promises';
import http from 'node:http';import {tmpdir} from 'node:os';import {join} from 'node:path';

const port=20000+Math.floor(Math.random()*20000),base=`http://127.0.0.1:${port}`;
let server,data;
const call=async(path,body,headers={})=>{const r=await fetch(base+path,{method:body?'POST':'GET',headers:{...(body?{'Content-Type':'application/json'}:{}),...headers},body:body?JSON.stringify(body):undefined});return {status:r.status,headers:r.headers,body:r.headers.get('content-type')?.includes('json')?await r.json():await r.arrayBuffer()};};
async function until(id,stage){
 for(let i=0;i<600;i++){const j=(await call('/api/jobs/'+id)).body;if(j.error)assert.fail(j.error);if(j.stage===stage&&!j.busy)return j;await new Promise(r=>setTimeout(r,100));}
 assert.fail('never reached '+stage);
}
before(async()=>{
 data=await mkdtemp(join(tmpdir(),'pod-studio-test-'));
 server=spawn(process.execPath,['server.mjs'],{env:{...process.env,PORT:String(port),REHEARSAL:'true',REHEARSAL_SPEED:'3000',OBSERVE_INTERVAL_MS:'40',DATA_DIR:data,STUDIO_NAME:'Test Studio',CLOUD_AGENT_ID:'',CLOUD_ENVIRONMENT_ID:''},stdio:['ignore','pipe','inherit']});
 await new Promise((ok,fail)=>{server.stdout.on('data',d=>String(d).includes('http://')&&ok());server.on('exit',c=>fail(Error('server exited '+c)));});
});
after(async()=>{server.kill();await rm(data,{recursive:true,force:true});});

test('status names the studio and the mode, never the former client',async()=>{
 const s=(await call('/api/status')).body;
 assert.deepEqual([s.brand.name,s.rehearsal,s.live],['Test Studio',true,true]);
 assert.ok(s.options.products.includes('Tumbler')&&s.options.languages.vi==='Vietnamese');
 for(const path of ['/','/app.js','/style.css']){const page=await call(path);assert.equal(page.status,200);assert.doesNotMatch(Buffer.from(page.body).toString(),/szmarketing|\bsz\b/i,path);}
 assert.match((await call('/')).headers.get('content-security-policy'),/script-src 'self'/);
});
test('only this machine and this page may use the interface',async()=>{
 assert.equal((await call('/api/jobs',{name:'x'},{Origin:'http://evil.example'})).status,403);
 const status=await new Promise(done=>http.get({host:'127.0.0.1',port,path:'/api/status',headers:{Host:'evil.example'}},r=>done(r.statusCode)));
 assert.equal(status,403);
 for(const path of ['/sample/media/../../.env','/sample/media/%2e%2e/server.mjs','/server.mjs','/data/jobs.json'])assert.equal((await call(path)).status,404,path);
 assert.equal((await call('/api/jobs/not-a-job')).status,404);
});
test('a whole campaign: research, five designs, the customer\'s choice, production and review',async()=>{
 const made=await call('/api/jobs',{name:'Walkthrough',product:'Poster',platform:'Facebook',brief:'ignored in rehearsal',max_rounds:5});
 assert.equal(made.status,201);
 const id=made.body.id;
 assert.deepEqual([made.body.stage,made.body.rehearsal,made.body.brief.product,made.body.limits.max_rounds,made.body.brief.name],['draft',true,'Mug',2,'Walkthrough']);
 assert.equal((await call(`/api/jobs/${id}/select`,{selected:['v1']})).status,409);
 assert.equal((await call(`/api/jobs/${id}/start`,{})).status,202);
 assert.equal((await call(`/api/jobs/${id}/start`,{})).status,409);

 const chosen=await until(id,'choosing');
 assert.equal(chosen.explore.variants.length,5);
 assert.equal(chosen.explore.research.sources.length,14);
 assert.deepEqual([chosen.brief.store,chosen.explore.research.competitor_designs.some(c=>/macorner/i.test(c.brand+c.url))],['macorner.co',false]);
 assert.equal(new Set(chosen.explore.variants.map(v=>v.style)).size,5);
 assert.deepEqual(chosen.explore.screening.report.recommended,['v1','v3','v2']);
 assert.equal(chosen.cloud.explore.preview.length,5);
 assert.ok(chosen.cloud.explore.activity.some(a=>a.kind==='store')&&chosen.cloud.explore.activity.some(a=>a.tone==='warn'));
 assert.equal((await call('/api/jobs')).body.find(j=>j.id===id).stage,'choosing');

 for(const selected of [[],['v1','v2','v3','v4'],['v1','v1'],['v9'],'v1'])assert.equal((await call(`/api/jobs/${id}/select`,{selected})).status,409,JSON.stringify(selected));
 assert.equal((await call(`/api/jobs/${id}/start`,{})).status,409);
 assert.equal((await call(`/api/jobs/${id}/select`,{selected:['v5','v4']})).status,202);

 const done=await until(id,'done');
 assert.deepEqual(done.final.variants.map(v=>[v.id,v.status,v.best_round,v.rounds.length]),[['v5','completed',2,2],['v4','completed',1,1]]);
 assert.equal(done.final.winner,'v5');
 const [first,second]=done.final.variants[0].rounds;
 assert.deepEqual([first.review.quality_gate,first.review.blocking_checks,first.design.reused],['blocked',['name_exact'],true]);
 assert.deepEqual([second.review.quality_gate,second.design.url,second.design.reused,second.probe.has_audio],['passed','/sample/media/design-v5-r2.png',undefined,true]);
 assert.match(second.changes,/ALEX/);
 assert.equal((await call(`/api/jobs/${id}/select`,{selected:['v1']})).status,409);

 const stored=JSON.parse(await readFile(join(data,'jobs.json'),'utf8'));
 assert.equal(stored[id].stage,'done');
 assert.equal((await call(`/api/jobs/${id}/archive`,{})).status,200);
 assert.equal((await call('/api/jobs/'+id)).status,404);
});
test('the sample opens once and its media can be played in ranges',async()=>{
 const a=await call('/api/sample',{}),b=await call('/api/sample',{});
 assert.deepEqual([a.status,b.status,a.body.id===b.body.id,a.body.sample],[201,200,true,true]);
 assert.equal((await call(`/api/jobs/${a.body.id}/start`,{})).status,409);
 const whole=await call('/sample/media/video-v1-r1.mp4'),part=await call('/sample/media/video-v1-r1.mp4',null,{Range:'bytes=0-99'}),tail=await call('/sample/media/video-v1-r1.mp4',null,{Range:'bytes=-50'});
 assert.deepEqual([whole.status,whole.headers.get('content-type'),part.status,part.body.byteLength,tail.body.byteLength],[200,'video/mp4',206,100,50]);
 assert.equal(part.headers.get('content-range'),`bytes 0-99/${whole.body.byteLength}`);
 assert.equal((await call('/sample/media/video-v1-r1.mp4',null,{Range:'bytes=999999999-'})).status,416);
 for(const v of a.body.final.variants)for(const r of v.rounds)for(const k of ['design','mockup','video'])assert.equal((await call(r[k].url)).status,200,r[k].url);
});
