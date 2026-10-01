export const PRODUCTS=['Mug','Tumbler','T-shirt','Hoodie','Tote bag','Canvas print','Blanket','Pillow','Ornament','Phone case','Poster'];
export const PLATFORMS=['TikTok','Instagram Reels','Facebook','YouTube Shorts'];
export function jsonObject(text){
  const clean=text.trim().replace(/^```(?:json)?\s*/,'').replace(/\s*```$/,'');
  const value=JSON.parse(clean); if(!value||typeof value!=='object'||Array.isArray(value))throw Error('Expected JSON object from MA');return value;
}
// The customer's own shop, as a bare domain such as macorner.co. Empty when not given.
export function storeOf(value){
  if(value===undefined||value===null||value==='')return '';
  if(typeof value!=='string'||value.length>200)throw Error('Invalid store');
  let host;try{host=new URL(/^https?:\/\//i.test(value.trim())?value.trim():'https://'+value.trim()).hostname.toLowerCase().replace(/^www\./,'');}catch{throw Error('Enter your store as a domain, such as yourstore.com');}
  if(!/^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$/.test(host))throw Error('Enter your store as a domain, such as yourstore.com');
  return host;
}
export function validateBrief(b){
  if(!b||!PRODUCTS.includes(b.product)||!PLATFORMS.includes(b.platform))throw Error('Invalid product or platform');
  for(const k of ['name','brief'])if(typeof b[k]!=='string'||!b[k].trim()||b[k].length>4000)throw Error('Missing or oversized '+k);
  // The brief itself names the market and buyer; this field is only an optional hint.
  const audience=b.audience??'';if(typeof audience!=='string'||audience.length>400)throw Error('Oversized audience');
  return {name:b.name.trim().slice(0,100),product:b.product,platform:b.platform,audience:audience.trim(),brief:b.brief.trim(),...(storeOf(b.store)?{store:storeOf(b.store)}:{})};
}
export function turnResult(events,messageId){
  const start=events.findIndex(e=>e.id===messageId);if(start<0)return null;
  let text=null;
  for(const e of events.slice(start+1)){
    if(e.type==='user.interrupt')throw Error('Cloud turn was interrupted; no successful completion');
    if(e.type==='user.message')throw Error('Another message interrupted the expected turn');
    if(e.type==='session.error')throw Error(JSON.stringify(e.error||e));
    if(e.type==='agent.message')text=(e.content||[]).filter(c=>c.type==='text').map(c=>c.text).join('');
    if(e.type==='session.status_idle'&&text)return text;
    if(/requires_action|terminated/.test(e.type))throw Error('MA needs attention: '+e.type);
  }return null;
}
