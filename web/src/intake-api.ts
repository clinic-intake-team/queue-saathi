export type Answer={red_flag?:{alert:boolean;keyword_flags?:string[];llm_flags?:string[]};question:string;transcript:string;extracted:Record<string,Field>;clip_url?:string|null;synthetic_mock:boolean;source:string;validation_errors?:{field:string;error:string}[]}
export type Field = {value:unknown; status:string; evidence:string; clip_url?:string|null}
export type Medicine = {name:string|null; strength:string|null; purpose?:string|null; display:string; status:string}
export type Question = {id:string; text:string; audio_url?:string; audio_followup_url?:string|null; audio_is_silent_mock:boolean; audio_error?:string|null; step:number; total_steps:number}
export type Session = {intake_complete?:boolean;stopped_at?:string;flow?:{routine_visit?:boolean;no_current_symptoms?:boolean;duration_not_applicable?:boolean;skip_followups?:boolean;applicability_reason?:string};question_language?:'hi'|'en'|'hinglish';ui_language?:'hi'|'en'|'hinglish';id:string; mock:boolean; status:string; question:Question; question_id:string; retry:boolean; medicines:Medicine[]; fields:Record<string,Field>; transcript?:string; done?:boolean; red_flag:{alert:boolean;status:string}; answers:Answer[]}
export class APIError extends Error {status:number;constructor(message:string,status:number){super(message);this.status=status}}
export async function request<T>(path:string,init:RequestInit={}):Promise<T>{
  const response=await fetch('/api'+path,init)
  if(!response.ok){let message='Your answer could not be saved. Please try again.';try{const body=await response.json();if(typeof body.detail==='string')message=body.detail}catch{/* server returned no JSON */}throw new APIError(message,response.status)}
  return response.json()
}
export function sampleWav(){
  const length=3200;const buffer=new ArrayBuffer(44+length*2);const view=new DataView(buffer)
  function text(offset:number,value:string){for(let i=0;i<value.length;i++)view.setUint8(offset+i,value.charCodeAt(i))}
  text(0,'RIFF');view.setUint32(4,36+length*2,true);text(8,'WAVE');text(12,'fmt ');view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,16000,true);view.setUint32(28,32000,true);view.setUint16(32,2,true);view.setUint16(34,16,true);text(36,'data');view.setUint32(40,length*2,true)
  return new Blob([buffer],{type:'audio/wav'})
}
export type Screen = 'question'|'recording'|'transcript'|'readback'|'red-flag'|'needs-check'|'done'|'unclear'
export const screens:Screen[]=['question','recording','transcript','readback','red-flag','needs-check','done','unclear']
export function sampleSession(screen:Screen):Session{
  const question:Question={id:'P2',text:'Aaj aap kis takleef ke liye aaye hain? Apne shabdon mein bataiye.',step:3,total_steps:9,audio_is_silent_mock:true}
  let status='in_progress'
  if(screen==='readback')Object.assign(question,{id:'R1',text:'Aapne bataya: Dolo 650, BP medicine (name unknown). Kya yeh sahi hai?',step:7})
  if(screen==='unclear')Object.assign(question,{id:'P1',text:'Maaf kijiye, theek se samajh nahi aaya. Ek baar phir bataiye? Aapki umar kitni hai?',step:2})
  if(screen==='red-flag'||screen==='needs-check'){question.id='RF';question.text='Yeh zaroori lag raha hai. Kripya abhi reception par bataiye.';status=screen==='red-flag'?'red_flag':'needs_check'}
  if(screen==='done'){question.id='P8';question.text='Shukriya! Aapki jaankari doctor tak pahunch gayi hai.';question.step=9;status='ready'}
  return {id:'sample',mock:true,status,question,question_id:question.id,retry:screen==='unclear',medicines:[{name:'Dolo',strength:'650',display:'Dolo 650',status:'needs_confirmation'},{name:null,strength:null,purpose:'BP',display:'BP medicine (name unknown)',status:'unknown_name_with_purpose'}],fields:{token:{value:18,status:'ok',evidence:'Mera token atharah hai.'}},red_flag:{alert:screen==='red-flag'||screen==='needs-check',status:screen==='needs-check'?'needs_check':'alert'},answers:[],transcript:'Kal raat se gale mein kharaash aur halki khaansi hai.'}
}
