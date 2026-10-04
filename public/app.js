// Interface text is English. Everything the agent wrote is shown as delivered, in the campaign's report language.
const $=(s,el=document)=>el.querySelector(s),$$=(s,el=document)=>[...el.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon=(name,cls='')=>`<i data-lucide="${name}"${cls?` class="${cls}"`:''}></i>`;
const STEPS=['brief','research','designs','mockups','videos','review'];
const STEP={brief:['Brief','file-text'],research:['Research','telescope'],designs:['Designs','palette'],mockups:['Mockups','image'],videos:['Videos','clapperboard'],review:['Review','shield-check']};
const PRODUCT_ICON={Mug:'coffee',Tumbler:'cup-soda','T-shirt':'shirt',Hoodie:'shirt','Tote bag':'shopping-bag','Canvas print':'frame',Blanket:'bed-double',Pillow:'sofa',Ornament:'tree-pine','Phone case':'smartphone',Poster:'image'};
const CHANNEL={amazon:['Amazon','shopping-cart'],etsy:['Etsy','store'],competitor_store:['Competitor stores','shopping-bag'],tiktok:['TikTok','music'],pinterest:['Pinterest','pin'],meta_ads:['Meta ads','megaphone'],trends:['Seasonal trends','trending-up'],industry:['Industry guides','book-open'],other:['Other','globe']};
const WINDOW={plan:['Plan ahead','info'],launch_now:['List now','brand'],in_market:['In market','good'],last_call:['Last call','warn']};
const OUTCOME={completed:['Accepted','good','badge-check'],max_rounds:['Best available','warn','flag'],blocked:['Blocked','bad','octagon-alert'],failed:['Did not finish','bad','circle-x'],running:['In production','violet','loader-circle'],needs_revision:['Revising','violet','rotate-ccw']};
const VERDICT={pass:['Pass','circle-check'],fail:['Fail','circle-x'],unverified:['Unverified','circle-help']};
const FEED={search:'search',read:'globe',store:'shopping-bag',calendar:'calendar-days',contract:'list-checks',select:'mouse-pointer-click',revise:'rotate-ccw',export:'package',design:'palette',screening:'trophy',mockup:'image',video_submit:'clapperboard',video:'film',evaluation:'eye',audit:'scale',adjudication:'gavel',review:'shield-check'};
const ASSET={design:'palette',mockup:'image',video:'clapperboard'};
const EXAMPLES=[
 {label:'Best-friend mug',name:'Botanical name mug · best-friend gift',product:'Mug',platform:'TikTok',brief:'Create an original personalized ceramic mug as a Christmas gift for a close friend. Target buyers are women aged 25-44 in the United States who love plants and calm, modern homes. The print shows the exact name ALEX with a botanical motif in blue. Deliver isolated flat print artwork on a plain white canvas, a lifestyle mockup with the print facing the camera, and a 5-second vertical product video with soft background sound. Keep the artwork and the ALEX lettering readable and consistent across all assets. No extra text, trademarks, invented claims or customer testimonials.'},
 {label:'Dog-mom tumbler',name:'Dog mom tumbler · holiday gift',product:'Tumbler',platform:'Instagram Reels',brief:"Design an original personalized tumbler for dog moms in the United States, women aged 28-45, as a Christmas gift from family. The print shows the exact text LUNA'S MOM with a hand-drawn golden retriever and a warm, playful feel. Deliver isolated flat print artwork on a plain white canvas, a lifestyle mockup with the print facing the camera, and a 5-second vertical product video with gentle background sound. Keep the text readable and consistent across all assets. No extra text, trademarks or invented claims."},
 {label:'Grandma ornament',name:"Nana's garden ornament",product:'Ornament',platform:'Facebook',brief:"Create an original personalized Christmas ornament for grandmothers in the United States, bought by their adult children aged 30-55. The print shows the exact text NANA'S GARDEN with four small flowers, one for each grandchild, in soft vintage colours. Deliver isolated flat print artwork on a plain white canvas, a lifestyle mockup on a Christmas tree with the print facing the camera, and a 5-second vertical product video with soft festive sound. No extra text, trademarks or invented claims."}];

const state={status:null,jobs:[],job:null,id:null,step:null,picks:{},round:{},focus:{},seen:{},view:null};
const painted=new Map();
const dateOf=new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric'}),clockOf=new Intl.DateTimeFormat('en-US',{hour:'numeric',minute:'2-digit',second:'2-digit'});
const day=s=>{const d=new Date(String(s).length===10?s+'T12:00:00':s);return isNaN(d)?esc(s):dateOf.format(d);};
const score=n=>Number.isFinite(n)?(Math.round(n*100)/100).toFixed(2).replace(/0$/,'').replace(/\.0$/,''):'–';
const plural=(n,word)=>`${n} ${word}${n===1?'':'s'}`;
const span=ms=>{const s=Math.max(0,Math.floor(ms/1000));return `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;};
// Only secure remote media or the bundled sample files are ever placed in the page.
function safe(value){
 if(typeof value!=='string')return '';
 if(/^\/sample\/media\/[a-z0-9-]+\.(jpg|png|svg|webp|mp4)$/.test(value))return value;
 try{const u=new URL(value);return u.protocol==='https:'?esc(u.href):'';}catch{return '';}
}
// Bundled sample videos ship with a poster frame beside them.
const posterOf=video=>safe(video?.poster)||(/^\/sample\/media\/video-/.test(video?.url||'')?video.url.replace('video-','poster-').replace('.mp4','.jpg'):'');
// Older reports may cite a store's JSON catalog feed; people should land on the store page instead.
function page(url){
 const link=safe(url);if(!link)return '';
 const m=/^(https:\/\/[^/]+)(\/collections\/[^/?]+)?\/products\.json\b/.exec(url);
 return m?esc(m[1]+(m[2]||'/collections/all')):link;
}
const hostOf=value=>{try{return new URL(value).hostname.replace(/^www\./,'');}catch{return '';}};
async function api(path,body){
 const r=await fetch(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});
 const x=await r.json().catch(()=>({}));if(!r.ok)throw Object.assign(Error(x.error||'Request failed'),{status:r.status});return x;
}
function toast(text){const t=$('#toast');t.textContent=text;t.classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>t.classList.remove('show'),5200);}
function paint(el,html){if(!el||painted.get(el)===html)return;painted.set(el,html);el.innerHTML=html;window.lucide?.createIcons();}
const pill=(text,tone='',ico='')=>`<span class="pill ${tone}">${ico?icon(ico):''}${esc(text)}</span>`;
const verdict=status=>`<span class="verdict ${esc(status)}">${icon(VERDICT[status]?.[1]||'circle-help')}${VERDICT[status]?.[0]||esc(status)}</span>`;
const bar=(value,max=5,tone='')=>`<span class="bar ${tone}"><i style="width:${Math.max(0,Math.min(100,value/max*100))}%"></i></span>`;
const outcome=status=>{const o=OUTCOME[status]||[status,'',''];return pill(o[0],o[1],o[2]);};
const details=(title,body)=>`<details class="prompt"><summary>${icon('chevron-right','chev')}${esc(title)}</summary><pre>${esc(body)}</pre></details>`;
function sources(job,ids){
 const all=job.explore?.research?.sources||[];
 return (ids||[]).map(id=>{const i=all.findIndex(s=>s.id===id),s=all[i];return s?`<a class="src" href="${page(s.url)||'#'}" target="_blank" rel="noopener noreferrer" title="${esc(s.title)}">${i+1}</a>`:'';}).join('');
}
function ring(value,tone){const r=54,c=2*Math.PI*r,v=Number.isFinite(value)?value:0;return `<div class="ring ${tone}"><svg viewBox="0 0 132 132" aria-hidden="true"><circle class="bg" cx="66" cy="66" r="${r}"/><circle class="fg" cx="66" cy="66" r="${r}" stroke-dasharray="${c.toFixed(1)}" stroke-dashoffset="${(c*(1-v/5)).toFixed(1)}"/></svg><div class="val"><b>${score(value)}</b><small>out of 5</small></div></div>`;}

// ---------- navigation ----------
function route(){
 const m=/^#\/c\/([a-f0-9-]+)(?:\/([a-z]+))?/.exec(location.hash);
 if(m){if(state.id!==m[1]){state.job=null;state.step=null;}state.id=m[1];if(STEPS.includes(m[2]))state.step=m[2];}
 else{state.id=null;state.job=null;state.step=null;}
}
const go=(id,step)=>{location.hash=id?`#/c/${id}${step?'/'+step:''}`:'#/';};
function landing(job){return job.stage==='choosing'?'designs':job.stage==='done'?'review':job.stage==='producing'?'mockups':'brief';}
// When the agent hands over, take the customer to the step that needs them.
function arrived(j){
 const before=state.seen[j.id];state.seen[j.id]=j.stage;
 if(!before||before===j.stage||j.error)return;
 if(j.stage==='choosing'){toast(`Your designs are ready. Choose up to ${j.limits.select_max}.`);go(j.id,'designs');}
 if(j.stage==='done'){toast('Everything is produced and reviewed.');go(j.id,'review');}
}
async function refresh(){
 try{
  state.jobs=await api('/api/jobs');
  if(state.id){
   try{state.job=await api('/api/jobs/'+state.id);}catch(e){if(e.status===404){toast('That campaign is no longer available');go();return;}throw e;}
   if(!state.step)state.step=landing(state.job);
   arrived(state.job);
  }
 }catch(e){if(!refresh.warned){toast(e.message);refresh.warned=true;}}
 render();
}

// ---------- shell ----------
function shell(){
 const s=state.status;if(!s)return;
 document.title=s.brand.name;$('#brandName').textContent=s.brand.name;$('#brandSpace').textContent=s.brand.workspace;
 $('#railMode').textContent=s.rehearsal?'Managed Agents':s.live?'Managed Agent in the cloud':'Connect the cloud agent to run live';
 paint($('#connection'),s.rehearsal?`<span class="dot good"></span><span>Ready</span>`:s.live?`<span class="dot good"></span><span>Live runs ready</span>`:s.configured?`<span class="dot warn"></span><span>Paid runs switched off</span>`:`<span class="dot warn"></span><span>Sample mode · not connected</span>`);
 $('#navHome').classList.toggle('active',!state.id);
 paint($('#railList'),state.jobs.slice(0,12).map(j=>`<a class="rail-item ${j.id===state.id?'active':''}" href="#/c/${j.id}"><span class="rail-thumb" style="${safe(j.cover)?`background-image:url('${safe(j.cover)}')`:''}">${safe(j.cover)?'':icon(PRODUCT_ICON[j.product]||'gift')}</span><span><b>${esc(j.name)}</b><small>${j.busy?'<span class="dot live"></span>':''}${esc(stageOf(j)[0])}</small></span></a>`).join('')||'<p class="muted small" style="padding:4px 12px">Nothing yet</p>');
}
function stageOf(j){
 if(j.failed||j.error)return ['Needs attention','bad','triangle-alert'];
 return ({draft:['Draft','','pencil-line'],exploring:['Researching & designing','violet','loader-circle'],choosing:['Your turn · choose designs','brand','mouse-pointer-click'],producing:['In production','violet','loader-circle'],done:['Finished','good','circle-check']})[j.stage]||[j.stage,'',''];
}
function render(){
 shell();
 const main=$('#main'),view=state.id?'ws:'+state.id:'home';
 if(state.view!==view){
  state.view=view;painted.clear();
  main.innerHTML=state.id?`<div class="view"><div id="wsHead"></div><div id="wsNotice"></div><div id="wsAgent"></div><div id="wsSteps"></div><div id="wsPanel" class="panel"></div></div>`:`<div class="view" id="home"></div>`;
  window.scrollTo({top:0});
 }
 if(!state.id)return paint($('#home'),home());
 const j=state.job;
 if(!j)return paint($('#wsPanel'),`<div class="card"><div class="ghosted" style="aspect-ratio:5/1">${icon('loader-circle','spin')}</div></div>`);
 paint($('#wsHead'),head(j));paint($('#wsNotice'),notices(j));paint($('#wsAgent'),j.busy?agent(j):'');paint($('#wsSteps'),stepper(j));
 paint($('#wsPanel'),({brief,research,designs,mockups,videos,review})[state.step](j));
}

// ---------- home ----------
function home(){
 const jobs=state.jobs,s=state.status||{};
 const cards=jobs.map(j=>{const st=stageOf(j);return `<a class="campaign" href="#/c/${j.id}"><div class="cover" style="${safe(j.cover)?`background-image:url('${safe(j.cover)}')`:''}">${safe(j.cover)?'':icon(PRODUCT_ICON[j.product]||'gift')}${pill(st[0],st[1]||'dark',st[2])}</div><div class="body"><h3>${esc(j.name)}</h3><div class="meta">${pill(j.product,'',PRODUCT_ICON[j.product]||'gift')}${pill(j.platform)}${j.sample?pill('Sample','violet','flask-conical'):''}</div><div class="meta">${Number.isFinite(j.score)?`${icon('award')}<b>${score(j.score)}</b> / 5 best score`:j.busy?'The agent is working…':'Created '+day(j.created)}</div></div></a>`;}).join('');
 return `<section class="hero">
  <div><span class="eyebrow">Print-on-demand creative studio</span>
   <h1>Turn a gift idea into a <em>launch-ready campaign</em>.</h1>
   <p class="lead">Write one brief. Your creative agent studies the market, designs ${s.live?'five':'five'} directions in different styles, then turns your favourites into product mockups and short videos with sound — each checked against your brief by independent reviewers.</p>
   <div class="hero-actions"><button class="btn accent large" data-action="compose">${icon('wand-sparkles')}Start a campaign</button><button class="btn large" data-action="sample">${icon('flask-conical')}Explore the sample</button></div>
  </div>
  <div class="collage" aria-hidden="true">
   <figure class="c1"><img src="/sample/media/design-v3.png" alt=""><figcaption>Print design</figcaption></figure>
   <figure class="c2"><img src="/sample/media/mockup-v1-r1.jpg" alt=""><figcaption>Mockup</figcaption></figure>
   <figure class="c3"><img src="/sample/media/poster-v2-r2.jpg" alt=""><figcaption>Video</figcaption></figure>
  </div>
 </section>
 <section class="steps4">
  ${[['telescope','Market research','Marketplaces, competitor stores, social video and the gifting calendar, with every source listed.'],['palette','Five design directions','One brief, five visibly different styles, ranked by an independent reviewer.'],['mouse-pointer-click','You choose up to three','Pick the designs you like. Only those go into production.'],['shield-check','Mockups, videos and review','Each result is scored against your brief and revised until it passes.']].map(([i,t,d],n)=>`<div class="how"><span class="num">${icon(i)}</span><span class="eyebrow">Step ${n+1}</span><h3>${t}</h3><p>${d}</p></div>`).join('')}
 </section>
 <div class="section-head"><div><h2>Campaigns</h2><p>${jobs.length?plural(jobs.length,'campaign')+' in this workspace':'Your campaigns will appear here'}</p></div><button class="btn" data-action="compose">${icon('plus')}New campaign</button></div>
 ${jobs.length?`<div class="cards">${cards}</div>`:`<div class="empty-state">${icon('sparkles')}<h3>Your next collection starts here</h3><p>Create a campaign, or open the sample to see a finished one.</p><div class="hero-actions"><button class="btn primary" data-action="compose">Create a campaign</button><button class="btn" data-action="sample">Open the sample</button></div></div>`}`;
}

// ---------- workspace frame ----------
function head(j){
 const st=stageOf(j),lang=state.status?.options.languages[j.limits.language]||j.limits.language;
 return `<div class="ws-head"><div><a class="crumb" href="#/">${icon('arrow-left')}All campaigns</a><h1>${esc(j.brief.name)}</h1>
  <div class="tags">${pill(st[0],st[1]||'dark',j.busy?'':st[2])}${pill(j.brief.product,'',PRODUCT_ICON[j.brief.product]||'gift')}${pill(j.brief.platform,'','clapperboard')}${j.explore?pill(j.explore.insights.market,'','map-pin'):''}${pill('Report in '+lang,'','languages')}${j.sample?pill('Sample','violet','flask-conical'):''}</div></div>
  <div class="ws-actions"><button class="btn" data-action="export">${icon('download')}Export</button>${j.busy?'':`<button class="icon-btn" data-action="archive" title="Remove from this workspace" aria-label="Remove from this workspace">${icon('archive')}</button>`}</div></div>`;
}
function notices(j){
 let out='';
 if(j.error)out+=`<div class="notice bad">${icon('triangle-alert')}<div><b>The run stopped before it finished.</b> ${esc(j.error)}</div>${j.sample||!state.status?.live?'':`<button class="btn" data-action="start">${icon('refresh-cw')}Resume watching</button>`}</div>`;
 if(j.stage==='choosing'&&!j.busy&&!j.sample&&state.step!=='designs')out+=`<div class="notice good">${icon('palette')}<div><b>Your designs are ready.</b> Choose up to ${j.limits.select_max} to turn into mockups and videos.</div><button class="btn" data-action="step" data-step="designs">Choose designs${icon('arrow-right')}</button></div>`;
 for(const w of j.explore?.warnings||[])out+=`<div class="notice warn">${icon('info')}<div>${esc(w)}</div></div>`;
 return out;
}
function stepper(j){
 const e=j.explore,f=j.final,n=j.selection?.length;
 const info={
  brief:[j.stage==='draft'?'':'done',`${j.brief.product} · ${j.brief.platform}`],
  research:[e?'done':j.busy&&j.stage==='exploring'?'live':'locked',e?plural(e.research.sources.length,'source'):'Waiting'],
  designs:[j.stage==='choosing'?'todo':n?'done':j.busy&&j.stage==='exploring'?'live':'locked',j.stage==='choosing'?`Choose up to ${j.limits.select_max}`:e?plural(e.variants.filter(v=>v.design).length,'direction'):'Waiting'],
  mockups:[f?'done':j.stage==='producing'?'live':'locked',n?plural(n,'design'):'Waiting'],
  videos:[f?'done':j.stage==='producing'?'live':'locked',n?`${plural(n,'video')} · ${j.limits.generate_audio?'sound on':'silent'}`:'Waiting'],
  review:[f?'done':j.stage==='producing'?'live':'locked',f?`Best ${score(bestOf(f.variants.find(v=>v.id===f.winner))?.review.score)} / 5`:'Waiting']};
 return `<nav class="stepper" aria-label="Campaign steps">${STEPS.map((s,i)=>{const [mode,sub]=info[s];return `<button class="step ${mode} ${state.step===s?'current':''}" data-action="step" data-step="${s}"><span class="bubble">${mode==='done'?icon('check'):mode==='live'?icon('loader-circle','spin'):icon(STEP[s][1])}</span><span><b>${STEP[s][0]}</b><small>${esc(sub)}</small></span></button>`;}).join('')}</nav>`;
}
const found=t=>t.id==='tech_duration'&&Number.isFinite(parseFloat(t.actual))?parseFloat(t.actual).toFixed(1)+' seconds':t.actual;
const bestOf=v=>v?.rounds.find(r=>r.number===v.best_round)||null;

// ---------- agent at work ----------
function agent(j){
 const phase=j.stage==='producing'?'produce':'explore',p=j.cloud?.[phase]||{},feed=p.activity||[],kinds=k=>feed.filter(a=>k.includes(a.kind));
 const made=kind=>feed.filter(a=>a.kind===kind&&a.tone==='good').length,chosen=j.selection?.length||0;
 let rows;
 if(phase==='explore'){
  const looked=kinds(['search','read','store','calendar']).length,frozen=kinds(['contract']).length,designs=made('design'),ranked=made('screening');
  rows=[['Read the brief',1,true],['Research the market',looked?`${looked} lookups`:'',frozen>0],['Write acceptance criteria','',designs>0||feed.some(a=>a.kind==='design')],[`Generate ${j.limits.design_count} designs`,designs?`${designs} of ${j.limits.design_count}`:'',ranked>0],['Rank the designs','',false]];
 }else{
  const reviewed=kinds(['review']).length;
  rows=[['Lock in your choices','',feed.some(a=>a.kind==='select')],['Create mockups',made('mockup')?`${made('mockup')} done`:'',made('video_submit')>0],['Render videos with sound',made('video')?`${made('video')} done`:'',made('evaluation')>0],['Independent review',reviewed?`${reviewed} verdict${reviewed===1?'':'s'}`:'',false],['Revise what did not pass',kinds(['revise']).length?`${kinds(['revise']).length} revision`:'',false]];
 }
 const at=rows.findIndex(r=>!r[2]);
 return `<section class="agent"><div>
   <span class="live-tag"><span class="dot live"></span>${j.rehearsal?'Working':'Working in the cloud'}</span>
   <h3>${phase==='explore'?'Your agent is studying the market and sketching designs':`Your agent is producing ${plural(chosen,'design')}`}</h3>
   <p>${phase==='explore'?`It reads marketplaces, competitor stores and trend reports, then designs in different styles. ${j.rehearsal?'This takes about a minute.':'This usually takes 8 to 15 minutes.'}`:`Mockups first, then videos, then independent reviewers score every result against your brief. ${j.rehearsal?'This takes a minute or two.':'Expect 10 to 20 minutes.'}`} Keep this app open to collect the results.</p>
   <div class="track">${rows.map((r,i)=>`<div class="track-row ${i<at||at<0?'done':i===at?'now':''}"><span class="mark">${i<at||at<0?icon('check'):i===at?icon('loader-circle','spin'):icon('circle')}</span><span>${esc(r[0])}</span><small>${esc(r[1]===1?'':r[1])}</small></div>`).join('')}</div>
   <div class="stats"><span>Elapsed <b data-since="${esc(p.started||'')}">0:00</b></span><span>Cloud events <b>${j.cloud?.event_count||0}</b></span>${j.session?`<span>Session <b>${esc(String(j.session).slice(0,18))}</b></span>`:''}</div>
  </div><div><div class="feed-title"><span>Live activity</span><span>${feed.length} steps</span></div><div class="feed">${feedItems(feed.slice(-9).reverse())||'<div class="feed-item"><span class="ico">'+icon('loader-circle','spin')+'</span><span>Starting the cloud session…</span><time></time></div>'}</div></div></section>`;
}
const feedItems=items=>items.map(a=>`<div class="feed-item ${esc(a.tone)}"><span class="ico">${icon(FEED[a.kind]||'circle-dot')}</span><span>${esc(a.text)}</span><time>${a.at?clockOf.format(new Date(a.at)):''}</time></div>`).join('');
setInterval(()=>{for(const el of $$('[data-since]')){const t=Date.parse(el.dataset.since);if(t)el.textContent=span(Date.now()-t);}},1000);

// ---------- brief ----------
function brief(j){
 const l=j.limits,lang=state.status?.options.languages[l.language]||l.language,e=j.explore;
 const tiles=[['palette','Design directions',l.design_count],['mouse-pointer-click','You take forward','Up to '+l.select_max],['rotate-ccw','Revision rounds','Up to '+l.max_rounds],['target','Quality target',l.target_score+' / 5'],[l.generate_audio?'volume-2':'volume-x','Video sound',l.generate_audio?'On':'Off'],['stamp','AI watermark',l.watermark?'On':'Off'],['languages','Report language',lang],['ratio','Video format','5 s · 9:16']];
 let out=`<section class="split"><div class="card"><div class="card-head"><div><h3>Your brief</h3><p>Exactly as you wrote it. Reviewers judge every result against these words.</p></div></div><p class="quote">${esc(j.brief.brief)}</p>${j.brief.store?`<p class="small muted" style="margin-top:12px">Your store: ${esc(j.brief.store)} · studied for your style, never treated as a competitor</p>`:''}${j.brief.audience?`<p class="small muted" style="margin-top:12px">Audience note: ${esc(j.brief.audience)}</p>`:''}</div>
  <div class="card"><h3>Run settings</h3><p class="sub">Fixed for the whole campaign.</p><div class="grid two">${tiles.map(t=>`<div class="tile"><small>${icon(t[0])}${t[1]}</small><b>${esc(t[2])}</b></div>`).join('')}</div></div></section>`;
 if(j.stage==='draft'&&!j.busy&&!j.error)out+=launch(j);
 if(e){
  const ins=e.insights,rows=[['map-pin','Market',ins.market],['users','Buyer',ins.audience],['gift','Occasion',ins.occasion],['heart','Recipient',ins.recipient],['palette','Tone',ins.tone],['pen-tool','Personalization',ins.personalization]].filter(r=>r[2]);
  out+=`<div class="card"><h3>What the agent understood</h3><p class="sub">Read from your brief before any research began.</p><div class="grid auto">${rows.map(r=>`<div class="insight"><span class="ico">${icon(r[0])}</span><div><small>${r[1]}</small><p>${esc(r[2])}</p></div></div>`).join('')}</div></div>`;
  out+=criteria(j);
 }
 const log=['explore','produce'].flatMap(p=>j.cloud?.[p]?.activity||[]);
 if(log.length&&!j.busy)out+=`<details class="card log"><summary class="card-head" style="cursor:pointer;margin:0"><div><h3>Run log</h3><p>${plural(log.length,'step')} the agent took, newest last.</p></div>${icon('chevron-down')}</summary><div class="feed" style="margin-top:16px">${feedItems(log)}</div></details>`;
 return out;
}
function launch(j){
 const live=state.status?.live;
 return `<section class="launch"><div><h3>${live?'Ready when you are':'Connect the cloud agent to run this'}</h3>
  <p>${live?`Your agent will research the market and generate ${j.limits.design_count} design directions. You choose which ones continue.`:'This campaign is saved. Live runs need the Managed Agent IDs and paid runs enabled in the .env file. Meanwhile, the sample shows a complete campaign.'}</p>
  <ul>${j.rehearsal?`<li>${icon('timer')}About one minute</li>`:`<li>${icon('timer')}About 8–15 minutes</li><li>${icon('cloud')}Runs in the cloud</li><li>${icon('coins')}Uses paid model calls</li>`}</ul></div>
  ${live?`<button class="btn accent large" data-action="start">${icon('play')}Start research &amp; designs</button>`:`<button class="btn large" data-action="sample">${icon('flask-conical')}Open the sample</button>`}</section>`;
}
function criteria(j){
 const list=j.explore.criteria,total=list.reduce((s,c)=>s+c.weight,0),audit=j.explore.contract_audit;
 return `<div class="card"><div class="card-head"><div><h3>Acceptance criteria</h3><p>Written from your brief and frozen before anything was generated. ${audit?.status==='completed'?`An independent auditor checked them ${audit.attempts>1?audit.attempts+' times':'once'}.`:''}</p></div>${pill(plural(list.filter(c=>c.required).length,'required check'),'dark','lock')}</div>
  ${audit?.report?.summary?`<p class="answer" style="margin-bottom:14px">${icon('scale')} ${esc(audit.report.summary)}</p>`:''}
  <div class="table-wrap"><table><thead><tr><th>What must be true</th><th>From your brief</th><th>Checked on</th><th>Type</th><th class="num">Weight</th></tr></thead><tbody>
  ${list.map(c=>`<tr><td><span class="main">${esc(c.label||c.description)}</span>${c.label?`<span class="sub">${esc(c.description)}</span>`:''}</td><td class="evidence"><span class="sub">“${esc(c.source_requirement)}”</span></td><td><span class="assets">${c.asset_refs.map(a=>`<span title="${a}">${icon(ASSET[a])}</span>`).join('')}</span></td><td>${c.required?pill('Required','dark'):pill('Preference')}</td><td class="num">${Math.round(c.weight/total*100)}%${bar(c.weight,Math.max(...list.map(x=>x.weight)))}</td></tr>`).join('')}
  </tbody></table></div></div>`;
}

// ---------- research ----------
const waiting=(j,title,text,ico)=>`<div class="card empty-state">${icon(j.busy?'loader-circle':ico,j.busy?'spin':'')}<h3>${title}</h3><p>${text}</p></div>`;
function research(j){
 const e=j.explore;if(!e)return waiting(j,j.busy?'Research is under way':'Research starts with the run',j.busy?'Sources, competitor designs and the gifting calendar will appear here as soon as the agent reports back.':'Open the Brief step and start the run to see the market study.','telescope');
 const r=e.research,cal=r.seasonal_calendar||[],focus=new Set((r.seasonal_focus||[]).map(f=>f.calendar_id).filter(Boolean));
 const stores=new Set(r.sources.filter(s=>s.channel==='competitor_store').map(s=>hostOf(s.url))).size;
 // The agent lists its focus occasions in order of importance; the rest of the calendar stays chronological.
 const aims=(r.seasonal_focus||[]).map(f=>cal.find(o=>o.id===f.calendar_id)).filter(Boolean);
 const key=aims[0]||cal.find(o=>o.gift_intensity==='peak')||cal[0],horizon=Math.max(1,...cal.map(o=>o.days_until)),shown=[...cal.filter(o=>focus.has(o.id)),...cal.filter(o=>!focus.has(o.id))];
 const section=(title,sub,body,extra='')=>body?`<div class="card"><div class="card-head"><div><h3>${title}</h3><p>${sub}</p></div>${extra}</div>${body}</div>`:'';
 return `<div class="grid four">${[['book-open',r.sources.length,'sources read and listed'],['lightbulb',(r.opportunities||[]).length,'design ideas from the evidence'],['shopping-bag',stores,'competitor stores studied'],['calendar-clock',key?key.days_until:'–',key?'days to '+key.name:'no occasion in range']].map(k=>`<div class="kpi"><span class="ico">${icon(k[0])}</span><b>${esc(k[1])}</b><span>${esc(k[2])}</span></div>`).join('')}</div>
 <div class="card"><div class="card-head"><div><h3>The agent's read of the market</h3><p>Written from the sources below.</p></div>${r.status==='complete'?pill('Full study','good','circle-check'):pill('Limited study','warn','triangle-alert')}</div><p class="answer">${esc(r.summary)}</p>${r.limitations?`<p class="small muted" style="margin-top:10px">${esc(r.limitations)}</p>`:''}</div>
 ${cal.length?section('Gifting calendar','Upcoming US occasions and how much selling time is left. Dates are computed; planning windows are rules of thumb.',`<div class="timeline"><span class="today">Today</span><span class="end">+${horizon} days</span><span class="rail-line"></span>${cal.map(o=>`<span class="pin ${o.gift_intensity==='peak'?'peak':''} ${focus.has(o.id)?'focus':''}" style="left:${(o.days_until/horizon*100).toFixed(1)}%" title="${esc(o.name)} · ${day(o.date)} · in ${o.days_until} days"></span>`).join('')}</div>
   <div class="occasions">${shown.map(o=>{const w=WINDOW[o.window]||[o.window,''];return `<div class="occasion ${focus.has(o.id)?'focus':''}"><div class="when"><b>${day(o.date)}</b><span>in ${o.days_until} days</span></div><h4>${esc(o.name)}</h4><div class="tags">${pill(w[0],w[1])}${o.gift_intensity==='peak'?pill('Peak gifting','dark','flame'):''}${focus.has(o.id)?pill('Campaign focus','brand','target'):''}</div><dl><dt>List by</dt><dd>${day(o.listing_live_by)}</dd><dt>Ads from</dt><dd>${day(o.ads_start_by)}</dd>${o.order_cutoff_estimate?`<dt>Order cutoff, est.</dt><dd>${day(o.order_cutoff_estimate)}</dd>`:''}</dl></div>`;}).join('')}</div>
   ${(r.seasonal_focus||[]).length?`<div class="table-wrap" style="margin-top:6px"><table><thead><tr><th>Occasion to aim for</th><th>Why</th><th>Sources</th></tr></thead><tbody>${r.seasonal_focus.map(f=>`<tr><td><span class="main">${esc(f.occasion)}</span></td><td>${esc(f.why)}</td><td>${sources(j,f.source_ids)||pill('Hypothesis','warn')}</td></tr>`).join('')}</tbody></table></div>`:''}`):''}
 ${section('Competitor designs worth studying','Described from titles and listed attributes. Themes are inspiration; nothing is copied.',(r.competitor_designs||[]).length?`<div class="grid auto">${r.competitor_designs.map(c=>`<div class="rival"><div class="brandline"><b>${esc(c.brand)}</b></div><h4>${esc(c.product||'')}</h4><div class="tags">${(c.style_tags||[]).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div><p>${esc(c.why_it_works)}</p><div class="tags" style="align-items:center">${c.signal?pill(c.signal,'info','activity'):''}${sources(j,c.source_ids)}${safe(c.url)?`<a class="link" href="${safe(c.url)}" target="_blank" rel="noopener noreferrer">Open listing${icon('external-link')}</a>`:''}</div></div>`).join('')}</div>`:'')}
 ${section('Words buyers and sellers use','Useful for listing titles and ad copy.',(r.keywords||[]).length?`<div class="table-wrap"><table><thead><tr><th>Term</th><th>What we saw</th><th>Sources</th></tr></thead><tbody>${r.keywords.map(k=>`<tr><td><span class="main">${esc(k.term)}</span></td><td>${esc(k.note)}</td><td>${sources(j,k.source_ids)||pill('Hypothesis','warn')}</td></tr>`).join('')}</tbody></table></div>`:'')}
 ${section('From insight to design direction','How the evidence shaped the five designs.',(r.opportunities||[]).length?`<div class="grid two">${r.opportunities.map((o,i)=>`<div class="idea"><span class="n">${i+1}</span><div><h4>${esc(o.title)}</h4><p>${esc(o.insight||'')}</p><div class="dir">${icon('arrow-right')}<span>${esc(o.design_direction)}</span></div><div style="margin-top:8px">${sources(j,o.source_ids)||pill('Hypothesis','warn')}</div></div></div>`).join('')}</div>`:'')}
 ${section('Source list',`All ${r.sources.length} sources, numbered as cited above.`,`<div class="table-wrap"><table class="ledger"><thead><tr><th>#</th><th>Source</th><th>What it shows</th></tr></thead><tbody>${r.sources.map((s,i)=>`<tr><td><span class="src">${i+1}</span></td><td><a class="link" href="${page(s.url)||'#'}" target="_blank" rel="noopener noreferrer">${esc(s.title)}</a><span class="sub">${esc(hostOf(s.url))} · ${day(s.retrieved)}</span><div class="tags">${pill((CHANNEL[s.channel]||[s.channel])[0],'',(CHANNEL[s.channel]||[])[1])}</div></td><td>${esc(s.finding)}</td></tr>`).join('')}</tbody></table></div>`)}`;
}

// ---------- designs ----------
function picksOf(j){return state.picks[j.id]||=[];}
function designs(j){
 const e=j.explore;
 if(!e){
  const ready=j.busy?j.cloud?.explore?.preview||[]:[];
  if(!ready.length)return waiting(j,j.busy?'Designs are on their way':'Designs come after research',j.busy?`The agent is preparing ${j.limits.design_count} directions in different styles.`:'Start the run from the Brief step.','palette');
  return `<div class="card"><div class="card-head"><div><h3>Designs are arriving</h3><p>${ready.length} of ${j.limits.design_count} ready. You choose once an independent reviewer has ranked them.</p></div>${pill('Preview · not reviewed yet','warn','hourglass')}</div></div>
   <div class="gallery">${ready.map(v=>`<article class="design"><button class="art" data-action="zoom" data-src="${safe(v.rounds[1]?.design)}" data-title="${esc(v.title||'Design '+v.id.slice(1))}" data-note="${esc(v.style||'Preview')}"><img src="${safe(v.rounds[1]?.design)}" alt="${esc(v.title||'Design preview')}"></button><div class="body"><div class="tags">${v.style?pill(v.style,'violet'):''}</div><h3>${esc(v.title||'Design '+v.id.slice(1))}</h3></div></article>`).join('')}${Array.from({length:Math.max(0,j.limits.design_count-ready.length)},()=>`<article class="design"><div class="ghosted">${icon('loader-circle','spin')}<span>Drawing…</span></div></article>`).join('')}</div>`;
 }
 const s=e.screening?.status==='completed'?e.screening.report:null,choosing=j.stage==='choosing'&&!j.busy&&!j.sample,picks=picksOf(j),taken=j.selection||[],max=j.limits.select_max;
 const order=s?[...s.ranking].sort((a,b)=>b.score-a.score).map(x=>x.id):[];
 const cards=e.variants.map(v=>{
  const img=safe(v.design?.url),rank=s?.ranking.find(x=>x.id===v.id),place=order.indexOf(v.id)+1,picked=choosing?picks.includes(v.id):taken.includes(v.id),n=(choosing?picks:taken).indexOf(v.id)+1;
  return `<article class="design ${picked?'picked':''} ${!choosing&&taken.length&&!picked?'dim':''}">
   ${img?`<button class="art" data-action="zoom" data-src="${img}" data-title="${esc(v.title)}" data-note="${esc(v.style)}"><img src="${img}" alt="${esc(v.title)}, ${esc(v.style)}" loading="lazy"><span class="badges"><span>${place?`<span class="rank">#${place}</span>`:''}</span><span>${picked?pill((choosing?'Your pick ':'Chosen ')+n,'brand','check'):s?.recommended.includes(v.id)?pill("Reviewer's pick",'dark','trophy'):''}</span></span></button>`:`<div class="art" style="cursor:default;display:grid;place-items:center;padding:24px;text-align:center"><div class="failnote">${icon('circle-x')}<b>This design was not generated</b><span>${esc(v.error)}</span></div></div>`}
   <div class="body"><div class="tags">${pill(v.style,'violet')}</div><h3>${esc(v.title)}</h3><p>${esc(v.rationale)}</p>
    ${v.palette?.length?`<div class="swatches">${v.palette.map(c=>`<i style="background:${esc(c)}" title="${esc(c)}"></i>`).join('')}${v.typography?`<span>${esc(v.typography)}</span>`:''}</div>`:''}
    ${rank?`<div class="scoreline"><span>Reviewer score</span>${bar(rank.score)}<b>${score(rank.score)} / 5</b></div><div class="tags" style="align-items:center"><span class="small muted">Spelling of the print text</span>${verdict(rank.text_check)}</div>
    <div class="pros"><div class="up">${icon('thumbs-up')}<span>${esc(rank.strengths)}</span></div><div class="down">${icon('triangle-alert')}<span>${esc(rank.risks)}</span></div><div class="for">${icon('users')}<span>${esc(rank.best_for)}</span></div></div>`:''}
    ${v.inspired_by?.length?`<div class="tags" style="align-items:center"><span class="small muted">Inspired by</span>${sources(j,v.inspired_by)}</div>`:''}
    ${details('See the design prompt',v.prompts.design)}</div>
   ${choosing&&img?`<button class="pick" data-action="pick" data-id="${v.id}">${icon(picked?'check':'plus')}${picked?'Chosen':'Choose this design'}</button>`:''}</article>`;}).join('');
 return `<div class="card"><div class="card-head"><div><h3>${plural(e.variants.length,'direction')}, one brief</h3><p>${choosing?`Choose up to ${max}. Only your choices become mockups and videos.`:taken.length?`You took ${plural(taken.length,'design')} into production.`:'Each direction uses a different style.'}</p></div>${s?pill('Ranked by an independent reviewer','info','eye'):pill('Ranking unavailable','warn')}</div>${s?`<p class="answer">${esc(s.summary)}</p>`:'<p class="muted small">The reviewer did not return a usable ranking. The designs are still yours to choose from.</p>'}</div>
  <div class="gallery">${cards}</div>
  ${choosing?`<div class="pickbar"><div class="left"><div class="thumbs">${picks.map(id=>`<img src="${safe(e.variants.find(v=>v.id===id).design.url)}" alt="">`).join('')}</div><div><b>${picks.length} of ${max} chosen</b><small>${picks.length?'In your order of preference':'Tap a design to choose it'}</small></div></div><div class="actions">${s?.recommended.length?`<button class="btn ghost" data-action="use-picks">${icon('trophy')}Use reviewer's picks</button>`:''}<button class="btn accent" data-action="confirm-picks" ${picks.length&&state.status?.live?'':'disabled'}>${icon('clapperboard')}Create mockups &amp; videos</button></div></div>`:''}`;
}

// ---------- production ----------
function roundOf(v,scope){const k=scope+':'+v.id,n=state.round[k];return v.rounds.find(r=>r.number===n)||bestOf(v)||v.rounds.at(-1);}
function lanes(j,scope,draw){
 const f=j.final;
 if(!f){
  if(j.stage!=='producing')return waiting(j,scope==='mockups'?'Mockups come after your choice':'Videos come after your choice',j.stage==='choosing'?'Choose your designs first.':'This step opens once designs are chosen.',STEP[scope][1]);
  const kind=scope==='mockups'?'mockup':'video';
  return `<div class="lanes">${(j.selection||[]).map(id=>{
   const v=j.explore.variants.find(x=>x.id===id),seen=(j.cloud?.produce?.preview||[]).find(x=>x.id===id)?.rounds||{};
   const n=Object.keys(seen).map(Number).sort((a,b)=>b-a).find(k=>safe(seen[k][kind])),url=n?safe(seen[n][kind]):'';
   const body=!url?`<div class="ghosted ${scope==='videos'?'tall':''}">${icon('loader-circle','spin')}<span>${scope==='videos'?'Rendering':'Composing'}…</span></div>`
    :scope==='videos'?`<div class="player"><video controls playsinline preload="metadata" ${posterOf({url})?`poster="${posterOf({url})}"`:''} src="${url}"></video></div>`
    :`<button class="shot" data-action="zoom" data-src="${url}" data-title="${esc(v.title)}" data-note="Mockup preview · round ${n}"><img src="${url}" alt="Mockup preview of ${esc(v.title)}"><span class="zoom">${icon('maximize-2')}</span></button>`;
   return `<article class="lane"><header class="lane-head"><img src="${safe(v.design.url)}" alt=""><div><h3>${esc(v.title)}</h3><small>${esc(v.style)}</small></div>${outcome('running')}</header><div class="stage">${body}${url?`<div class="facts">${pill('Preview · review pending','warn','hourglass')}${n>1?pill('Round '+n,'info'):''}</div>`:''}</div></article>`;}).join('')}</div>`;
 }
 return `<div class="lanes">${f.variants.map(v=>{
  const r=roundOf(v,scope),design=safe(v.rounds[0]?.design?.url);
  return `<article class="lane ${v.id===f.winner?'winner':''}"><header class="lane-head"><img src="${design}" alt=""><div><h3>${esc(v.title)}</h3><small>${esc(v.style)}${v.id===f.winner?' · top result':''}</small></div>${outcome(v.status)}</header>
   ${v.rounds.length>1?`<div class="rounds">${v.rounds.map(x=>`<button class="round ${x===r?'on':''}" data-action="round" data-scope="${scope}" data-id="${v.id}" data-n="${x.number}">Round ${x.number}${x.review?icon(x.review.quality_gate==='passed'?'check':'x'):''}${x.number===v.best_round?' · kept':''}</button>`).join('')}</div>`:''}
   <div class="stage">${draw(v,r)}${r.number>1&&r.changes?`<div class="change">${icon('wand-sparkles')}<span><b>What changed in round ${r.number}:</b> ${esc(r.changes)}</span></div>`:''}${v.error&&r===v.rounds.at(-1)?`<div class="failnote"><b>This design stopped here</b><span>${esc(v.error)}</span></div>`:''}${details('See the prompt',r.prompts[scope==='mockups'?'mockup':'video'])}</div></article>`;}).join('')}</div>`;
}
function mockups(j){
 return lanes(j,'mockups',(v,r)=>{const img=safe(r.mockup?.url);return img?`<button class="shot" data-action="zoom" data-src="${img}" data-title="${esc(v.title)}" data-note="Mockup · round ${r.number}"><img src="${img}" alt="Mockup of ${esc(v.title)}" loading="lazy"><span class="zoom">${icon('maximize-2')}</span></button><div class="facts">${r.number===1?'':r.mockup.reused?pill('Kept from the previous round','','repeat'):pill('New in round '+r.number,'info','sparkles')}${r.design?.reused?pill('Your chosen artwork','brand','check'):pill('Artwork redrawn','warn','pencil-line')}</div>`:`<div class="ghosted">${icon('image-off')}<span>No mockup in this round</span></div>`;});
}
function videos(j){
 return lanes(j,'videos',(v,r)=>{const src=safe(r.video?.url),p=r.probe,t=r.review?.technical_checks||[];
  return src?`<div class="player"><video controls playsinline preload="metadata" ${posterOf(r.video)?`poster="${posterOf(r.video)}"`:''} src="${src}"></video></div>
   <div class="facts">${p&&!p.error?`${p.has_audio?pill('Sound on','good','volume-2'):pill('No sound','bad','volume-x')}${pill(`${Number(p.duration_seconds).toFixed(1)} s`,'','timer')}${pill(`${p.width}×${p.height}`,'','ratio')}`:pill('File not inspected','warn','circle-help')}</div>
   ${t.some(x=>x.status==='fail')?`<div class="failnote">${t.filter(x=>x.status==='fail').map(x=>`<span><b>${esc(x.name)}.</b> Expected ${esc(x.expected)}, found ${esc(x.actual)}.</span>`).join('')}</div>`:''}`:`<div class="ghosted tall">${icon('video-off')}<span>No video in this round</span></div>`;});
}

// ---------- review ----------
function review(j){
 const f=j.final;if(!f)return waiting(j,j.stage==='producing'?'Reviewers are waiting for the media':'The review comes last',j.stage==='producing'?'Scores appear here once every chosen design has been produced and judged.':'Independent reviewers score each produced design against your brief.','shield-check');
 const list=j.explore.criteria,passed=f.variants.filter(v=>v.status==='completed'),focus=f.variants.find(v=>v.id===state.focus[j.id])||f.variants.find(v=>v.id===f.winner)||f.variants[0];
 const tone=v=>v.status==='completed'?'':v.status==='max_rounds'?'warn':'bad';
 const thumb=v=>safe(bestOf(v)?.mockup?.url||v.rounds[0]?.design?.url);
 const cards=f.variants.map(v=>{const b=bestOf(v);return `<button class="score-card ${v.id===f.winner?'winner':''} ${v===focus?'on':''}" data-action="focus" data-id="${v.id}">${v.id===f.winner?`<span class="crown">${icon('crown')}Top result</span>`:''}<img src="${thumb(v)}" alt=""><div><h3>${esc(v.title)}</h3><small class="muted">${esc(v.style)}</small></div>${ring(b?.review.score,tone(v))}${outcome(v.status)}<div class="trend">${v.rounds.filter(r=>r.review).map(r=>`<span>Round ${r.number} <b>${score(r.review.score)}</b></span>`).join(icon('arrow-right'))||'<span>No score</span>'}</div></button>`;}).join('');
 const mark=(v,id)=>{const c=bestOf(v)?.review.checks.find(x=>x.id===id);return c?`<span class="cellmark">${verdict(c.status)}<small>${score(c.score)} / 5</small></span>`:'–';};
 const tech=[...new Map(f.variants.flatMap(v=>bestOf(v)?.review.technical_checks||[]).map(t=>[t.id,t])).values()];
 const group=(title,rows)=>rows.length?`<tr class="group"><td colspan="${f.variants.length+1}">${title}</td></tr>${rows.join('')}`:'';
 const matrix=`<div class="table-wrap"><table><thead><tr><th>Requirement</th>${f.variants.map(v=>`<th class="center">${esc(v.title)}${v.best_round?`<br><span class="muted" style="text-transform:none;letter-spacing:0;font-weight:500">round ${v.best_round}</span>`:''}</th>`).join('')}</tr></thead><tbody>
  ${group('Required',list.filter(c=>c.required).map(c=>`<tr><td><span class="main">${esc(c.label||c.description)}</span><span class="sub assets">${c.asset_refs.map(a=>icon(ASSET[a])).join('')}</span></td>${f.variants.map(v=>`<td class="center">${mark(v,c.id)}</td>`).join('')}</tr>`))}
  ${group('Preferences',list.filter(c=>!c.required).map(c=>`<tr><td><span class="main">${esc(c.label||c.description)}</span><span class="sub assets">${c.asset_refs.map(a=>icon(ASSET[a])).join('')}</span></td>${f.variants.map(v=>`<td class="center">${mark(v,c.id)}</td>`).join('')}</tr>`))}
  ${group('Measured on the video file',tech.map(t=>`<tr><td><span class="main">${esc(t.name)}</span></td>${f.variants.map(v=>{const x=(bestOf(v)?.review.technical_checks||[]).find(y=>y.id===t.id);return `<td class="center">${x?`<span class="cellmark">${verdict(x.status)}<small>${esc(found(x))}</small></span>`:'–'}</td>`;}).join('')}</tr>`))}
  <tr class="total"><td>Weighted score</td>${f.variants.map(v=>`<td class="center">${score(bestOf(v)?.review.score)} / 5</td>`).join('')}</tr>
  <tr class="total"><td>Result</td>${f.variants.map(v=>`<td class="center">${outcome(v.status)}</td>`).join('')}</tr></tbody></table></div>`;
 return `<section class="headline ${passed.length?'':'warn'}"><span class="big">${icon(passed.length?'party-popper':'flag')}</span><div><h3>${passed.length?`${passed.length} of ${f.variants.length} designs passed every required check`:'No design met the target yet'}</h3><p>${passed.length?`Target ${j.limits.target_score} / 5. A design is accepted only when every required check passes and its score reaches the target.`:`The best version of each design is kept for you. Target ${j.limits.target_score} / 5, up to ${plural(j.limits.max_rounds,'round')}.`}</p></div>${pill('Your approval is still needed before publishing','dark','user-check')}</section>
  <div class="podium">${cards}</div>
  <div class="card"><div class="card-head"><div><h3>At a glance</h3><p>The kept version of each design, judged on the same criteria.</p></div></div>${matrix}</div>
  ${detail(j,focus)}`;
}
function detail(j,v){
 const f=j.final,r=roundOf(v,'review'),w=r.review;
 const tabs=`<div class="segmented">${f.variants.map(x=>`<button class="${x===v?'on':''}" data-action="focus" data-id="${x.id}">${x.id===f.winner?icon('crown'):''}${esc(x.title)}</button>`).join('')}</div>`;
 const rounds=v.rounds.length>1?`<div class="rounds" style="padding:0">${v.rounds.map(x=>`<button class="round ${x===r?'on':''}" data-action="round" data-scope="review" data-id="${v.id}" data-n="${x.number}">Round ${x.number}${x.review?` · ${score(x.review.score)}`:''}${x.number===v.best_round?' · kept':''}</button>`).join('')}</div>`:'';
 if(!w)return `<div class="card"><div class="card-head"><div><h3>Findings in detail</h3><p>${esc(v.title)}</p></div>${tabs}</div>${rounds}<div class="failnote" style="margin-top:14px"><b>This round has no review</b><span>${esc(v.error||'The media for this round was not completed.')}</span></div></div>`;
 const open=w.conflicts||[];
 return `<div class="card"><div class="card-head"><div><h3>Findings in detail</h3><p>What the reviewer saw in the actual files, and what to change.</p></div>${tabs}</div>
  <div class="grid" style="gap:14px">${rounds}
  <div class="tags" style="align-items:center">${outcome(r.number===v.best_round?v.status:w.quality_gate==='passed'?'completed':'needs_revision')}${pill(`Score ${score(w.score)} / 5`,'dark','award')}${pill('Scored by an independent reviewer','info','eye')}${pill('Checked by an auditor','info','scale')}${open.length?pill(`${plural(open.length,'conflict')} settled by a second reviewer`,'violet','gavel'):''}</div>
  <p class="answer">${esc(w.summary)}</p>
  ${r.number>1&&r.changes?`<div class="change">${icon('wand-sparkles')}<span><b>What changed in round ${r.number}:</b> ${esc(r.changes)}</span></div>`:''}
  ${w.quality_gate==='passed'?'':`<div class="fix"><span class="ico">${icon('wrench')}</span><div><b>Most important fix</b>${esc(w.priority_fix)}</div></div>`}
  <div class="table-wrap"><table><thead><tr><th>Requirement</th><th>Result</th><th class="num">Score</th><th>What the reviewer saw</th><th>How to improve</th></tr></thead><tbody>
   ${w.checks.map(c=>`<tr><td><span class="main">${esc(c.label)}</span><span class="sub">${c.required?'Required':'Preference'} · ${c.asset_refs.map(a=>a).join(', ')}</span></td><td>${verdict(c.status)}</td><td class="num">${score(c.score)}${bar(c.score,5,c.status==='pass'?'good':c.status==='fail'?'bad':'warn')}</td><td class="evidence">${esc(c.evidence)}</td><td class="evidence">${esc(c.improvement)}</td></tr>`).join('')}
   ${w.technical_checks.length?`<tr class="group"><td colspan="5">Measured on the video file</td></tr>${w.technical_checks.map(t=>`<tr><td><span class="main">${esc(t.name)}</span></td><td>${verdict(t.status)}</td><td class="num">–</td><td>Found: ${esc(found(t))}</td><td>Expected: ${esc(t.expected)}</td></tr>`).join('')}`:''}
  </tbody></table></div>
  ${open.length?`<div class="table-wrap"><table><thead><tr><th>Disputed requirement</th><th>What the auditor questioned</th><th>Second reviewer's decision</th></tr></thead><tbody>${open.map(c=>`<tr><td><span class="main">${esc(w.checks.find(x=>x.id===c.id)?.label||c.id)}</span></td><td class="evidence">${esc(c.reason)}</td><td class="evidence">${c.resolved?pill('Settled','good','check'):pill('Left unverified','warn')} ${esc(c.resolution||'')}</td></tr>`).join('')}</tbody></table></div>`:''}
  </div></div>`;
}

// ---------- actions ----------
function openComposer(example){
 const f=$('#composerForm'),o=state.status.options;
 if(!$('#productChips').children.length){
  $('#productChips').innerHTML=o.products.map((p,i)=>`<label class="chip"><input type="radio" name="product" value="${esc(p)}" ${i?'':'checked'}>${icon(PRODUCT_ICON[p]||'gift')}${esc(p)}</label>`).join('');
  $('#platformChips').innerHTML=o.platforms.map((p,i)=>`<label class="chip"><input type="radio" name="platform" value="${esc(p)}" ${i?'':'checked'}>${esc(p)}</label>`).join('');
  $('#languageSelect').innerHTML=Object.entries(o.languages).map(([k,v])=>`<option value="${esc(k)}">${esc(v)}</option>`).join('');
  $('#examples').innerHTML=EXAMPLES.map((e,i)=>`<button type="button" data-action="example" data-i="${i}">${esc(e.label)}</button>`).join(' · ');
  window.lucide?.createIcons();
 }
 const fixed=state.status.rehearsal;
 if(fixed){const b=state.status.sample.brief;example={name:f.elements.name.value||b.name,brief:b.brief,product:b.product,platform:b.platform,store:b.store};}
 f.elements.store.readOnly=fixed;
 $('#composerNote').hidden=!fixed;$('#composerCost').textContent=fixed?'Saving is free.':'Saving is free. Generation starts only when you press Start, and uses paid model calls.';$('.advanced',f).hidden=fixed;f.elements.brief.readOnly=fixed;$('#examples').parentElement.hidden=fixed;
 for(const el of $$('#productChips input,#platformChips input',f))el.disabled=fixed&&!el.checked&&el.value!==example[el.name];
 if(example){f.elements.name.value=example.name;if(example.store!==undefined)f.elements.store.value=example.store;f.elements.brief.value=example.brief;f.elements.product.value=example.product;f.elements.platform.value=example.platform;}
 if(!$('#composer').open)$('#composer').showModal();
}
$('#composerForm').addEventListener('submit',async e=>{
 e.preventDefault();const f=e.target,d=Object.fromEntries(new FormData(f));
 try{
  const job=await api('/api/jobs',{name:d.name,product:d.product,platform:d.platform,brief:f.elements.brief.value,store:f.elements.store.value,audience:d.audience,language:d.language,max_rounds:Number(d.max_rounds),target_score:Number(d.target_score),design_count:Number(d.design_count),select_max:Number(d.select_max),generate_audio:f.elements.generate_audio.checked,watermark:f.elements.watermark.checked});
  $('#composer').close();f.reset();go(job.id,'brief');
 }catch(err){toast(err.message);}
});
const actions={
 compose:()=>openComposer(),
 'close-composer':()=>$('#composer').close(),
 'close-viewer':()=>$('#viewer').close(),
 example:el=>openComposer(EXAMPLES[Number(el.dataset.i)]),
 sample:async()=>{const j=await api('/api/sample',{});go(j.id,'research');},
 step:el=>go(state.id,el.dataset.step),
 start:async()=>{await api(`/api/jobs/${state.id}/start`,{});toast('The agent has started. You can follow its progress here.');await refresh();},
 pick:el=>{const j=state.job,p=picksOf(j),i=p.indexOf(el.dataset.id);if(i>=0)p.splice(i,1);else if(p.length>=j.limits.select_max)return toast(`You can take up to ${j.limits.select_max} designs forward. Unselect one first.`);else p.push(el.dataset.id);painted.delete($('#wsPanel'));render();},
 'use-picks':()=>{const j=state.job;state.picks[j.id]=j.explore.screening.report.recommended.slice(0,j.limits.select_max);painted.delete($('#wsPanel'));render();},
 'confirm-picks':async()=>{const j=state.job;await api(`/api/jobs/${j.id}/select`,{selected:picksOf(j)});toast('Production has started for your chosen designs.');go(j.id,'mockups');await refresh();},
 round:el=>{state.round[el.dataset.scope+':'+el.dataset.id]=Number(el.dataset.n);render();},
 focus:el=>{state.focus[state.id]=el.dataset.id;render();},
 zoom:el=>{$('#viewerBody').innerHTML=`<img src="${safe(el.dataset.src)}" alt=""><figcaption><b>${esc(el.dataset.title)}</b>${esc(el.dataset.note)}</figcaption>`;$('#viewer').showModal();},
 export:()=>{const j=state.job,a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(j,null,2)],{type:'application/json'}));a.download='campaign-export-'+j.id+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);},
 archive:async()=>{if(!confirm('Remove this campaign from the workspace? Its record stays in the local data file.'))return;await api(`/api/jobs/${state.id}/archive`,{});go();},
};
document.addEventListener('click',async e=>{
 const el=e.target.closest('[data-action]');if(!el||el.disabled)return;
 if(el.tagName!=='A')e.preventDefault();
 try{await actions[el.dataset.action]?.(el);}catch(err){toast(err.message);}
});
for(const d of $$('dialog'))d.addEventListener('click',e=>{if(e.target===d)d.close();});
window.addEventListener('hashchange',()=>{route();refresh();});

(async()=>{
 try{state.status=await api('/api/status');}catch(e){toast(e.message);}
 route();await refresh();
 setInterval(refresh,3000);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
})();
