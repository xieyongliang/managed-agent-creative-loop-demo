import {test} from 'node:test';import assert from 'node:assert/strict';import {execFileSync} from 'node:child_process';
import {validateBrief,jsonObject,turnResult,PRODUCTS} from './core.mjs';
import {cloudLimits,toolJson,cloudProgress,cloudActivity,cloudPreview,assertNoStateEdits,collectExport,validateCriteria,technicalChecks,evidenceReview,validateResearch,applyExplore,applyFinal,bestRound,winnerOf,runPhase} from './cloud.mjs';

// Manifests come from the real helper, so these tests fail if the bridge and the helper ever disagree.
const made=JSON.parse(execFileSync('python3',['test-fixtures.py'],{encoding:'utf8',maxBuffer:32e6}));
const copy=x=>structuredClone(x);
const brief={name:'Test',product:'Mug',platform:'TikTok',audience:'',brief:made.brief};
const draft=()=>({id:'11111111-2222-3333-4444-555555555555',brief:copy(brief),limits:cloudLimits(),stage:'draft',busy:false});
const explored=()=>{const j=draft();applyExplore(j,copy(made.explore));j.stage='choosing';return j;};
const chosen=()=>{const j=explored();j.selection=['v2','v4','v1'];return j;};
let calls=0;
const stdout=(...values)=>({type:'text',text:'exit_code: 0\n--- stdout ---\n'+values.map(v=>JSON.stringify(v)).join('\n')+'\n\n--- stderr ---\n'});
const bash=(command,...values)=>{const id='call-'+(++calls);return [{id,type:'agent.tool_use',name:'bash',input:{command}},{type:'agent.tool_result',tool_use_id:id,content:[stdout(...values)]}];};
const reply=text=>[{type:'agent.message',content:[{type:'text',text}]},{type:'session.status_idle'}];
const helper='python3 /mnt/skills/pod-creative-loop/scripts/creative.py ';

test('campaign settings are explicit, bounded and default to sound on',()=>{
 assert.deepEqual(cloudLimits(),{max_rounds:2,target_score:4.5,watermark:true,generate_audio:true,language:'vi',design_count:5,select_max:3});
 assert.deepEqual(cloudLimits({max_rounds:'3',target_score:'4',generate_audio:false,watermark:false,language:'en',design_count:6,select_max:2}),{max_rounds:3,target_score:4,watermark:false,generate_audio:false,language:'en',design_count:6,select_max:2});
 for(const bad of [{max_rounds:6},{target_score:NaN},{design_count:2},{design_count:7},{select_max:4},{select_max:0},{language:'fr'},{language:'constructor'},{watermark:'false'},{generate_audio:0}])assert.throws(()=>cloudLimits(bad),JSON.stringify(bad));
});
test('brief accepts any listed product and treats audience as an optional hint',()=>{
 assert.throws(()=>validateBrief({}));assert.throws(()=>validateBrief({product:'Other',platform:'TikTok'}));
 assert.throws(()=>validateBrief({name:'x',product:'Mug',platform:'TikTok',brief:'a'.repeat(4001)}));
 assert.throws(()=>validateBrief({name:'x',product:'Mug',platform:'TikTok',brief:'ok',audience:'a'.repeat(401)}));
 for(const product of PRODUCTS)assert.equal(validateBrief({name:' x ',product,platform:'Instagram Reels',brief:' gift '}).audience,'');
});
test('JSON only, no ambiguous prose extraction',()=>{assert.deepEqual(jsonObject('```json\n{"score":3}\n```'),{score:3});assert.throws(()=>jsonObject('Success {"score":3}'));});
test('old replies cannot complete a new turn',()=>{const old=[{type:'agent.message',content:[{type:'text',text:'old'}]},{type:'session.status_idle'},{id:'new',type:'user.message'}];assert.equal(turnResult(old,'new'),null);assert.equal(turnResult([...old,...reply('review')],'new'),'review');assert.equal(turnResult(old,'missing'),null);});
test('interrupted cloud turn cannot remain pending or report success',()=>{assert.throws(()=>turnResult([{type:'user.message',id:'u'},{type:'user.interrupt'},{type:'session.status_idle'}],'u'),/interrupted/);});

test('helper output is read line by line from stdout only',()=>{
 assert.deepEqual(toolJson({content:[stdout({a:1},{b:2})]}),[{a:1},{b:2}]);
 assert.deepEqual(toolJson({content:[{type:'text',text:'exit_code: 0\n--- stdout ---\nnot json\n{"a":1}\n--- stderr ---\n{"ignored":true}'}]}),[{a:1}]);
 assert.deepEqual(toolJson({content:[]}),[]);
});
test('cloud progress parses only structured helper stdout',()=>{
 assert.deepEqual(cloudProgress(bash(helper+'step',made.progress[2])),{status:'needs_revision',phase:'production',round:1,variants:[{id:'v2',status:'needs_revision',round:1,score:4.7},{id:'v4',status:'completed',round:1,score:4.7},{id:'v1',status:'needs_revision',round:1,score:4.7}]});
 assert.equal(cloudProgress(reply('{"status":"completed","round":1}')),null);
});
test('activity feed narrates research and production without raw tool output',()=>{
 const events=[{type:'agent.tool_use',name:'web_search',input:{query:'personalized mug gift trends'}},{type:'agent.tool_use',name:'web_fetch',input:{url:'https://www.example.com/best-sellers?x=1'}},
  ...bash('python3 research.py storefront --store shop.example.com',{status:'ok'}),...bash('python3 research.py calendar',{occasions:[]}),
  ...bash(helper+'step',{status:'variant_reviewed',round:2,log:[{unit:'design',variant:'v3',result:'ok'},{unit:'video',variant:'v1',result:'retry',detail:'InternalError'},{unit:'mockup',variant:'v2',result:'failed',detail:'refused'},{unit:'review',variant:'v1',round:2,result:'completed',detail:'score 4.8'}]})];
 assert.deepEqual(cloudActivity(events,{v1:'Botanical'}).map(x=>[x.kind,x.text,x.tone]),[
  ['search','Searching: personalized mug gift trends','info'],['read','Reading example.com','info'],['store','Reading the public catalog of shop.example.com','info'],['calendar','Checking upcoming US gifting occasions','info'],
  ['design','Design 3: artwork generated','good'],['video','Botanical: video service was busy, trying again','warn'],['mockup','Design 2: mockup did not complete','bad'],['review','Botanical (round 2): accepted · score 4.80','good']]);
});
test('finished assets are previewed while the run continues, and only from secure URLs',()=>{
 const events=[...bash(helper+'step',{status:'design_completed',round:1,log:[{unit:'design',variant:'v1',result:'ok',url:'https://example.com/d1.png',title:' Line  art ',style:'Botanical'},{unit:'design',variant:'v2',result:'failed',detail:'refused'},{unit:'design',variant:'v3',result:'ok',url:'http://example.com/d3.png'},{unit:'design',variant:'../x',result:'ok',url:'https://example.com/x.png'}]}),
  ...bash(helper+'step',{status:'video_completed',round:2,log:[{unit:'mockup',variant:'v1',round:2,result:'ok',url:'https://example.com/m.jpg'},{unit:'video',variant:'v1',round:2,result:'ok',url:'https://example.com/v.mp4'},{unit:'evaluation',variant:'v1',round:2,result:'ok',url:'https://example.com/ignored'}]}),
  ...reply('{"log":[{"unit":"design","variant":"v4","result":"ok","url":"https://example.com/narrative.png"}]}')];
 assert.deepEqual(cloudPreview(events),[{id:'v1',title:'Line art',style:'Botanical',rounds:{1:{design:'https://example.com/d1.png'},2:{mockup:'https://example.com/m.jpg',video:'https://example.com/v.mp4'}}}]);
});
test('direct state edits are rejected even if a final manifest looks valid',()=>{
 assert.throws(()=>assertNoStateEdits([{type:'agent.tool_use',name:'edit',input:{file_path:'/mnt/session/creative-loop/state.json'}}]));
 assert.throws(()=>assertNoStateEdits([{type:'agent.tool_use',name:'write',input:{path:'/mnt/skills/pod-creative-loop/scripts/evaluation.py'}}]));
 assert.throws(()=>assertNoStateEdits([{type:'agent.tool_use',name:'bash',input:{command:'echo {} > /mnt/session/creative-loop/state.json'}}]));
 assert.doesNotThrow(()=>assertNoStateEdits([{type:'agent.tool_use',name:'write',input:{file_path:'/mnt/session/campaign-plan.json'}},{type:'agent.tool_use',name:'bash',input:{command:'cat /mnt/session/creative-loop/state.json'}}]));
});

test('cloud completion must come from an export tool result',()=>{
 assert.deepEqual(collectExport(bash(helper+'export',made.explore)).manifest,made.explore);
 assert.equal(collectExport(reply(JSON.stringify(made.explore))).manifest,null);
 assert.equal(collectExport(bash('echo done',made.explore)).manifest,null);
 const failed=bash(helper+'export',made.explore);failed[1].is_error=true;assert.equal(collectExport(failed).manifest,null);
});
test('a chunked export is reassembled and verified',()=>{
 const parts=made.parts.map(p=>bash(helper+'export --chunk 1000 --part '+p.export_part,p));
 const index=bash(helper+'export --chunk 1000',made.index);
 assert.deepEqual(collectExport([...parts.slice(3),...index,...parts.slice(0,3)].flat()).manifest,made.explore);
 assert.deepEqual(collectExport([...index,...parts.filter((_,i)=>i!==1&&i!==4).flat()]),{manifest:null,missing:[2,5],parts:made.index.parts});
 const bad=copy(made.parts);bad[0].data='x'+bad[0].data.slice(1);
 assert.throws(()=>collectExport([...index,...bad.flatMap(p=>bash(helper+'export --part '+p.export_part,p))]),/checksum/);
 assert.deepEqual(collectExport([...index,...bash(`for i in 1 2 3; do ${helper}export --part $i; done`,...made.parts)]).manifest,made.explore);
});

const rubric=()=>[{id:'delivery',description:'Requested deliverable',source_requirement:'Deliver it',required:true,priority:1,weight:1,asset_refs:['design']},{id:'style',description:'Preferred style',label:'Phong cách',source_requirement:'Prefer it',required:false,priority:2,weight:1,asset_refs:['mockup','video']}];
const sound={duration_seconds:5.04,width:720,height:1280,has_audio:true};
function evidenceRound(){
 const criteria=rubric(),report={summary:'Observed media',checks:criteria.map(c=>({id:c.id,status:'pass',score:5,evidence:'Observed',improvement:'Refine'})),uncovered_requirements:[],release_checks:[]};
 return {criteria,round:{probe:copy(sound),technical:technicalChecks(sound,true),evaluation:{response_id:'eval',report},audit:{response_id:'audit',report:{conflicts:[],uncovered_requirements:[]}},review:{score:5,quality_gate:'passed',blocking_checks:[],uncovered_requirements:[],priority_fix:'Refine'}}};
}
test('dynamic bridge validates arbitrary criterion IDs and carries display labels',()=>{const {criteria,round}=evidenceRound();const review=evidenceReview(round,criteria,true);assert.equal(review.quality_gate,'passed');assert.deepEqual(review.checks.map(c=>c.label),['Requested deliverable','Phong cách']);});
test('malformed criteria are refused',()=>{for(const change of [c=>c[0].weight=0,c=>c[0].asset_refs=['poster'],c=>c[1].id='delivery',c=>c[0].required=false,c=>c[0].label=' '])assert.throws(()=>{const c=rubric();change(c);validateCriteria(c);});});
test('creator cannot override independent failure with a pass',()=>{const {criteria,round}=evidenceRound();round.evaluation.report.checks[0].status='fail';assert.throws(()=>evidenceReview(round,criteria,true),/differs from independent/);});
test('conflicting report requires adjudication',()=>{const {criteria,round}=evidenceRound();round.audit.report.conflicts=[{id:'delivery',reason:'Evidence contradicts pass'}];assert.throws(()=>evidenceReview(round,criteria,true),/adjudication/);});
test('unresolved required conflict cannot pass',()=>{const {criteria,round}=evidenceRound();round.audit.report.conflicts=[{id:'delivery',reason:'Ambiguous evidence'}];round.adjudication={response_id:'judge',report:{...round.evaluation.report,resolutions:[{id:'delivery',resolved:false,reason:'Still uncertain'}]}};assert.throws(()=>evidenceReview(round,criteria,true),/differs from independent/);round.review.quality_gate='blocked';round.review.blocking_checks=['delivery'];const review=evidenceReview(round,criteria,true);assert.equal(review.checks[0].status,'unverified');assert.deepEqual(review.conflicts,[{id:'delivery',reason:'Ambiguous evidence',resolved:false,resolution:'Still uncertain'}]);});
test('optional failed preference does not block required gate',()=>{const {criteria,round}=evidenceRound();round.evaluation.report.checks[1].status='fail';assert.equal(evidenceReview(round,criteria,true).quality_gate,'passed');});
test('audit coverage gaps block acceptance',()=>{const {criteria,round}=evidenceRound();round.audit.report.uncovered_requirements=['Missing requirement'];assert.throws(()=>evidenceReview(round,criteria,true),/differs from independent/);round.review.quality_gate='blocked';round.review.uncovered_requirements=['Missing requirement'];assert.equal(evidenceReview(round,criteria,true).quality_gate,'blocked');});
test('review score uses frozen criterion weights',()=>{const {criteria,round}=evidenceRound();criteria[0].weight=3;round.evaluation.report.checks[0].score=4;round.review.score=4.5;assert.throws(()=>evidenceReview(round,criteria,true),/differs from independent/);round.review.score=4.25;assert.equal(evidenceReview(round,criteria,true).score,4.25);});
test('a silent video cannot be accepted when sound was requested',()=>{
 const {criteria,round}=evidenceRound();round.probe.has_audio=false;
 assert.throws(()=>evidenceReview(round,criteria,true),/differs from independent/);
 round.review.quality_gate='blocked';round.review.blocking_checks=['tech_audio'];
 assert.throws(()=>evidenceReview(round,criteria,true),/Technical checks differ/);
 round.technical=technicalChecks(round.probe,true);
 assert.deepEqual(evidenceReview(round,criteria,true).technical_checks.map(t=>t.status),['fail','pass','pass']);
 assert.deepEqual(technicalChecks({error:'expired'},true).map(t=>t.status),['unverified']);
 assert.equal(technicalChecks(round.probe,false)[0].status,'pass');
});

test('research must cite its sources and admit thin coverage',()=>{
 const good=()=>copy(made.explore.research);
 assert.equal(validateResearch(good()).size,8);
 for(const change of [r=>r.sources[0].url='http://example.com',r=>r.sources[1].id='s1',r=>r.keywords[0].source_ids=['nope'],r=>r.sources[2].url='https://shop.example.com/products.json?limit=60',r=>r.competitor_designs[0].source_ids=[],r=>r.coverage=r.coverage.slice(1),r=>{r.sources=r.sources.filter(s=>s.channel!=='amazon');r.keywords=[];},r=>r.status='limited',r=>delete r.seasonal_calendar])
  assert.throws(()=>{const r=good();change(r);validateResearch(r);},String(change));
});
test('the customer\'s own store is never shown as a competitor',()=>{
 assert.doesNotThrow(()=>validateResearch(copy(made.explore.research),'shop.test.com'));
 const own=copy(made.explore.research);own.sources[2].url='https://www.example.com/collections/all';
 assert.throws(()=>validateResearch(own,'example.com'),/own store/);
 const named=copy(made.explore.research);named.competitor_designs[0].brand='Macorner';
 assert.throws(()=>validateResearch(named,'macorner.co'),/own store/);
 const j=draft();j.brief.store='example.com';
 assert.throws(()=>applyExplore(j,{...copy(made.explore),research:own}),/own store/);
 assert.equal(validateBrief({...brief,store:'https://www.MyShop.com/collections/all'}).store,'myshop.com');
 assert.equal(validateBrief(brief).store,undefined);
 assert.throws(()=>validateBrief({...brief,store:'not a store'}),/domain/);
});
test('design exploration manifest from the helper is accepted',()=>{
 const j=explored();
 assert.deepEqual(j.explore.variants.map(v=>v.id),['v1','v2','v3','v4','v5']);
 assert.deepEqual(j.explore.warnings,[]);
 assert.equal(j.explore.screening.report.ranking.length,5);
});
test('design exploration manifest must match the campaign',()=>{
 const reject=(change,pattern,job=draft())=>assert.throws(()=>{const m=copy(made.explore);change(m,job);applyExplore(job,m);},pattern);
 reject(m=>m.generate_audio=false,/generate audio/);
 reject(m=>m.design_count=6,/design count/);
 reject(m=>m.schema=2,/current Skill/);
 reject(m=>m.status='failed',/ended as failed/);
 reject(m=>m.variants.pop(),/requested number/);
 reject(m=>m.variants[2].design.url='http://example.com/x.png',/lacks a generated image/);
 reject(m=>m.variants[1].style=m.variants[0].style,/different styles/);
 reject(m=>m.variants.forEach(v=>{delete v.design;v.error='refused';}),/No design/);
 reject(m=>m.screening.report.ranking[0].score=7,/screening/);
 reject(m=>m.screening.report.recommended=['v1','v2','v3','v4'],/screening/);
 reject(m=>m.variants[0].inspired_by=['s99'],/malformed/);
 reject(m=>delete m.insights.audience,/insights/);
});
test('a refused design and unavailable screening are shown, not hidden',()=>{
 const j=draft(),m=copy(made.explore);delete m.variants[4].design;m.variants[4].error='Design generation was refused';m.screening={status:'unavailable'};
 applyExplore(j,m);assert.equal(j.explore.variants[4].error,'Design generation was refused');
});
test('a reworded brief and uncovered requirements are surfaced as warnings',()=>{
 const j=draft(),m=copy(made.explore);m.brief='A different brief';m.contract_audit={status:'completed',attempts:3,report:{summary:'x',gaps:[{requirement:'No music',suggestion:'Add it'}],unsupported:[]}};
 applyExplore(j,m);assert.equal(j.explore.warnings.length,2);assert.match(j.explore.warnings[1],/No music/);
});

test('final manifest from the helper is accepted and reviews are rebuilt',()=>{
 const j=chosen();applyFinal(j,copy(made.final));
 assert.deepEqual(j.final.variants.map(v=>[v.id,v.status,v.best_round,v.rounds.length]),[['v2','completed',2,2],['v4','completed',1,1],['v1','max_rounds',1,2]]);
 assert.equal(j.final.winner,'v2');assert.equal(j.final.met_target,true);
 const first=j.final.variants[0].rounds[0].review;
 assert.deepEqual([first.quality_gate,first.review_source,first.blocking_checks,first.checks[0].status,first.checks[0].label],['blocked','adjudication',['delivery'],'fail','Giao đúng sản phẩm yêu cầu']);
 assert.deepEqual(first.conflicts,[{id:'delivery',reason:'The evidence says missing but the verdict says pass',resolved:true,resolution:'Actual asset lacks the deliverable'}]);
 assert.equal(j.final.variants[0].title,'Concept 2');
 assert.equal(j.final.variants[0].rounds[1].changes,'Làm rõ chữ in');
});
test('final manifest must match the selection, contract and evidence',()=>{
 const reject=(change,pattern)=>assert.throws(()=>{const j=chosen(),m=copy(made.final);change(m,j);applyFinal(j,m);},pattern);
 reject((m,j)=>j.selection=['v2','v4'],/selection/);
 reject(m=>m.variants.reverse(),/selection/);
 reject(m=>m.contract_hash='changed',/contract changed/);
 reject(m=>m.max_rounds=5,/max rounds/);
 reject(m=>m.variants[0].rounds[0].design.url='https://example.com/other',/did not start from the design/);
 reject(m=>m.variants[1].rounds[0].review.score=5,/differs from independent/);
 reject(m=>m.variants[2].status='completed',/falsely claims|Campaign status|best-score/);
 reject(m=>m.variants[2].best_round=2,/best-score/);
 reject(m=>m.result_summary.winner='v4',/Result summary/);
 reject(m=>m.status='max_rounds',/Campaign status/);
 reject(m=>delete m.variants[1].rounds[0].audit,/evaluation and audit/);
 reject(m=>m.variants[1].rounds[0].video.url='http://example.com/v.mp4',/actual-media evidence/);
 reject(m=>m.variants[1].rounds[0].probe.has_audio=false,/differs from independent/);
 reject(m=>m.variants[0].rounds.push(copy(m.variants[0].rounds[1])),/round limit/);
});
test('round and winner selection follow the return policy',()=>{
 const round=(number,score,gate)=>({number,review:{score,quality_gate:gate}});
 assert.equal(bestRound({status:'max_rounds',rounds:[round(1,4.8,'blocked'),round(2,4.7,'passed')]}).number,2);
 assert.equal(bestRound({status:'max_rounds',rounds:[round(1,4,'blocked'),round(2,4,'blocked')]}).number,1);
 assert.equal(bestRound({status:'completed',rounds:[round(1,4.9,'passed'),round(2,4.6,'passed')]}).number,2);
 assert.equal(bestRound({status:'failed',rounds:[{number:1}]}),null);
 assert.equal(winnerOf([{id:'a',status:'max_rounds',rounds:[round(1,4.9,'blocked')]},{id:'b',status:'completed',rounds:[round(1,4.6,'passed')]},{id:'c',status:'completed',rounds:[round(1,4.6,'passed')]},{id:'d',status:'failed',rounds:[{number:1}]}]),'b');
 assert.equal(winnerOf([{id:'d',status:'failed',rounds:[{number:1}]}]),null);
});

// A stand-in for the CLI: accepted messages join the Session history, and the script decides how the agent answers.
function session(answer){
 const events=[],sent=[],log=[];
 return {events,sent,log,cli:async args=>{
  log.push(args.slice(2,4).join(' '));
  if(args[2]==='create')return {id:'sesn-test'};
  if(args[3]==='list')return {data:[...events]};
  const message={id:'msg-'+(sent.length+1),type:'user.message',content:[{type:'text',text:args[args.indexOf('--text')+1]}]};
  events.push(message);sent.push(message.content[0].text);events.push(...answer(sent.length,message.content[0].text));
  return {data:[message]};
 }};
}
const run=(job,phase,s)=>runPhase(job,phase,{cli:s.cli,save:async()=>{},pause:async()=>{},interval:0,today:'2026-09-30'});
process.env.CLOUD_AGENT_ID='agent-test';process.env.CLOUD_ENVIRONMENT_ID='env-test';

test('phase 1 sends the brief once and stops for the customer\'s choice',async()=>{
 const s=session(()=>[...bash(helper+'step',made.progress[1]),...bash(helper+'export',made.explore),...reply('{}')]),j=draft();
 await run(j,'explore',s);
 assert.equal(j.error,undefined);assert.deepEqual([j.stage,j.busy,j.session,s.sent.length],['choosing',false,'sesn-test',1]);
 assert.match(s.sent[0],/^\[campaign 11111111-2222-3333-4444-555555555555 · phase explore\]/);
 for(const needle of ['PHASE 1 of 2','Today is 2026-09-30','in Vietnamese','exactly 5 design variants',JSON.stringify(j.limits),JSON.stringify(j.brief)])assert.ok(s.sent[0].includes(needle),needle);
 assert.equal(j.cloud.progress.status,'awaiting_selection');assert.equal(j.explore.variants.length,5);
});
test('phase 2 sends only the selection and returns the verified result',async()=>{
 const s=session(()=>[...bash(helper+'select --input /mnt/session/selection.json',{status:'running',round:1}),...bash(helper+'export',made.final),...reply('{}')]),j=chosen();j.session='sesn-test';j.stage='producing';
 await run(j,'produce',s);
 assert.equal(j.error,undefined);assert.deepEqual([j.stage,j.final.winner,s.sent.length],['done','v2',1]);
 assert.ok(s.sent[0].includes('["v2","v4","v1"]'));assert.ok(!s.sent[0].includes(made.brief));
 assert.deepEqual(j.cloud.produce.activity.map(x=>x.kind),['select','export']);
 assert.ok(!s.log.includes('session create'));
});
test('missing export parts are requested again instead of accepting a narrative',async()=>{
 const part=i=>bash(helper+'export --part '+i,made.parts[i-1]),all=made.parts.map((_,i)=>i+1);
 const s=session(n=>n===1?[...bash(helper+'export',made.index),...all.filter(i=>i!==3).flatMap(part),...reply('All done')]:[...part(3),...reply('DONE')]),j=draft();
 await run(j,'explore',s);
 assert.equal(j.error,undefined);assert.equal(j.stage,'choosing');assert.equal(s.sent.length,2);
 assert.match(s.sent[1],/follow-up\nThe export is incomplete.*creative\.py export --part 3$/);
});
test('an agent that never exports ends in an error after bounded reminders',async()=>{
 const s=session(()=>reply('The campaign looks great, score 5/5!')),j=draft();
 await run(j,'explore',s);
 assert.match(j.error,/No successful cloud export/);assert.deepEqual([j.stage,j.busy,s.sent.length],['exploring',false,4]);
 assert.match(s.sent[2],/--chunk 6000/);assert.equal(j.explore,undefined);
});
test('a send with an unknown outcome is adopted, never repeated',async()=>{
 const s=session(()=>[]),j=draft();j.session='sesn-test';j.cloud={explore:{sendStarted:true}};
 const first=session(()=>[...bash(helper+'export',made.explore),...reply('{}')]);await run(draft(),'explore',first);
 s.events.push({id:'msg-early',type:'user.message',content:[{type:'text',text:first.sent[0]}]},...bash(helper+'export',made.explore),...reply('{}'));
 await run(j,'explore',s);
 assert.equal(j.error,undefined);assert.deepEqual([j.stage,s.sent.length,j.cloud.explore.first],['choosing',0,'msg-early']);
});
test('an unknown send that never arrived is sent once after a second look',async()=>{
 const s=session(()=>[...bash(helper+'export',made.explore),...reply('{}')]),j=draft();j.session='sesn-test';j.cloud={explore:{sendStarted:true}};
 await run(j,'explore',s);
 assert.deepEqual([j.stage,s.sent.length,s.log.filter(x=>x==='events list').length>=3],['choosing',1,true]);
});
test('a Session message from another campaign is not adopted',async()=>{
 const s=session(()=>[]),j=draft();j.session='sesn-test';j.cloud={explore:{sendStarted:true}};
 s.events.push({id:'msg-x',type:'user.message',content:[{type:'text',text:`[campaign ${j.id} · phase explore]\nsomething else`}]});
 await run(j,'explore',s);assert.match(j.error,/does not match this campaign/);
});
test('state tampering, interruptions and wrong settings stop the run',async()=>{
 const cases=[
  [()=>[{type:'agent.tool_use',name:'edit',input:{file_path:'/mnt/session/creative-loop/state.json'}},...bash(helper+'export',made.explore),...reply('{}')],/modified protected state/],
  [()=>[{type:'user.interrupt'},{type:'session.status_idle'}],/interrupted/],
  [()=>[{type:'session.error',error:{message:'model unavailable'}}],/model unavailable/],
  [()=>[...bash(helper+'export',{...made.explore,watermark:false}),...reply('{}')],/watermark/]];
 for(const [answer,pattern] of cases){const j=draft();await run(j,'explore',session(answer));assert.match(j.error,pattern);assert.deepEqual([j.stage,j.busy,j.explore],['exploring',false,undefined]);}
});
test('phase 2 cannot start without the Session of phase 1',async()=>{const j=chosen();await run(j,'produce',session(()=>[]));assert.match(j.error,/Session of this campaign is missing/);});
