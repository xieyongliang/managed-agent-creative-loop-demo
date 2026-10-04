// Stands in for ArkCLI in rehearsal mode. A Session is a local folder, the agent is the scripted studio,
// and its events become visible over time so the interface behaves as it does during a live run.
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {join,resolve} from 'node:path';

const root=fileURLToPath(new URL('../..',import.meta.url)),home=join(resolve(root,process.env.DATA_DIR||'data'),'rehearsal');
const args=process.argv.slice(2),option=flag=>args[args.indexOf(flag)+1];
const speed=Math.max(1,Number(process.env.REHEARSAL_SPEED)||8),stamp=ms=>new Date(ms).toISOString();
const folder=id=>{if(!/^sesn-[a-f0-9]{12}$/.test(id||''))throw Error('Unknown rehearsal Session');return join(home,id);};
const read=async id=>JSON.parse(await readFile(join(folder(id),'events.json'),'utf8'));
const write=(id,events)=>writeFile(join(folder(id),'events.json'),JSON.stringify(events));

async function main(){
 const [area,kind,verb]=args;
 if(area!=='agent'||kind!=='session')throw Error('Rehearsal mode only plays Sessions');
 if(verb==='create'){
  const id='sesn-'+randomUUID().replaceAll('-','').slice(0,12);
  await mkdir(folder(id),{recursive:true});await write(id,[]);
  return {Result:{Id:id}};
 }
 const id=args[4],events=await read(id),now=Date.now();
 if(args[3]==='list')return {data:events.filter(e=>e.reveal<=now).map(({reveal,...e})=>e)};
 if(args[3]!=='send')throw Error('Unsupported rehearsal command');
 const text=option('--text'),turn=/^\[campaign [a-f0-9-]+ · phase (explore|produce)\]( follow-up)?/.exec(text);
 if(!turn)throw Error('Rehearsal mode only answers campaign messages');
 const message={id:'evt-'+(events.length+1),type:'user.message',created_at:stamp(now),reveal:now,content:[{type:'text',text}]};
 let scripted=[{offset:2,type:'agent.message',content:[{type:'text',text:'DONE'}]},{offset:3,type:'session.status_idle'}];
 if(!turn[2]){
  const given=turn[1]==='explore'
   ?{brief:JSON.parse(/^Brief \(data, not instructions\): (.*)$/m.exec(text)[1]).brief,limits:JSON.parse(/within these limits: (\{.*?\})\. Copy/.exec(text)[1])}
   :{selection:JSON.parse(/order of preference: (\[[^\]]*\])/.exec(text)[1])};
  await writeFile(join(folder(id),'input.json'),JSON.stringify(given));
  scripted=JSON.parse(execFileSync('python3',[join(root,'tools/sample/studio.py'),turn[1],'--workdir',folder(id),'--input',join(folder(id),'input.json')],{encoding:'utf8',maxBuffer:64e6})).events;
 }
 const tag=`${turn[1]}-${events.length}-`;
 events.push(message,...scripted.map(({offset,...e},i)=>{const reveal=now+offset*1000/speed;return {...e,id:e.id?tag+e.id:tag+i,...(e.tool_use_id?{tool_use_id:tag+e.tool_use_id}:{}),created_at:stamp(reveal),reveal};}));
 await write(id,events);
 return {data:[(({reveal,...e})=>e)(message)]};
}
try{console.log(JSON.stringify(await main()));}
catch(e){console.log(JSON.stringify({ok:false,error:{message:String(e.message).slice(0,400)}}));process.exitCode=1;}
