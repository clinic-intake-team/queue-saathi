/** Deterministic presentation from accepted fields. No model calls or transcript re-extraction. */
import type { Field, Session, Medicine, Answer } from './intake-api'
export type DoctorRecord=Session&{created_at:string;flow?:{routine_visit?:boolean;no_current_symptoms?:boolean;duration_not_applicable?:boolean;skip_followups?:boolean;applicability_reason?:string}}
export type Detail={key:string;label:string;text:string;evidence:{quote:string;clip?:string|null}[];medicines?:{text:string;confirmed:boolean;unknown:boolean}[]}
const labels:Record<string,string>={token:'Token',age:'Age',sex:'Sex',visit_reason:'Visit reason',complaint:'Complaint',duration_days:'Duration',duration_hours:'Duration',medicines:'Medicines',allergies:'Allergies',conditions:'Conditions',confirmed:'Medicine confirmation',follow_up:'Follow-ups',red_flag_symptoms:'Safety check'}
export const accepted=(field?:Field)=>field?.status==='ok'&&field.value!==null&&field.value!==undefined
const text=(field?:Field)=>accepted(field)&&typeof field!.value==='string'?field!.value.trim():''
const norm=(value:string)=>value.toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim()
const clean=(value:string)=>value.trim().replace(/[.!?。।]+$/u,'')
const capitalise=(value:string)=>value.replace(/(^|[.!?]\s+)(\p{Ll})/gu,(_match,prefix:string,letter:string)=>prefix+letter.toLocaleUpperCase())
const sentence=(value:string)=>value?capitalise(clean(value))+'.':''
const routinePattern=/routine|check[ -]?up|follow[ -]?up|monitoring|नियमित|चेक[ -]?अप|फॉलो/i
function complaint(field?:Field):{summary:string;symptoms:string[]}|null{
 if(!accepted(field)||typeof field!.value!=='object'||Array.isArray(field!.value))return null
 const v=field!.value as {summary?:unknown;symptoms?:unknown}
 return typeof v.summary==='string'&&Array.isArray(v.symptoms)&&v.symptoms.every(x=>typeof x==='string')?{summary:v.summary,symptoms:v.symptoms}:null
}
/** Combine accepted complaint phrases without repeating shared concepts. */
export function complaintPhrase(value:{summary:string;symptoms:string[]}){
 const stop=new Set('a an the and or with in on at of to this patient reports reported having has have'.split(' '))
 const words=(text:string)=>new Set(norm(text).split(' ').filter(word=>!stop.has(word)))
 const split=(text:string)=>{const match=clean(text).match(/^(.*?)(\s+(?:since|for|from)\s+.+)$/i);return match?{body:match[1],time:match[2]}:{body:clean(text),time:''}}
 const first=split(value.summary),phrases=[first.body];let timing=first.time
 for(const symptom of value.symptoms){
  const next=split(symptom);if(!timing)timing=next.time
  const tokens=words(next.body)
  if(!tokens.size||phrases.some(phrase=>[...tokens].every(token=>words(phrase).has(token))))continue
  const covered=phrases.findIndex(phrase=>[...words(phrase)].every(token=>tokens.has(token)))
  if(covered>=0)phrases[covered]=next.body;else phrases.push(next.body)
 }
 return capitalise(phrases.filter(Boolean).join('; ')+timing)
}
function evidence(...fields:(Field|undefined)[]){
 const result:Detail['evidence']=[]
 for(const f of fields)if(f?.evidence&&!result.some(e=>e.quote===f.evidence))result.push({quote:f.evidence,clip:f.clip_url})
 return result
}
function format(field?:Field):string{
 if(!accepted(field))return ''
 const value=field!.value
 if(typeof value==='string')return value==='none'?'None reported':value==='unknown'?'Unknown':value
 if(typeof value==='number')return String(value)
 if(typeof value==='boolean')return value?'Yes':'No'
 if(Array.isArray(value))return value.length?value.map(v=>typeof v==='string'?v:JSON.stringify(v)).join(', '):'None reported'
 if(typeof value==='object'&&value!==null&&'question_key' in value&&'value' in value){
  const follow=value as {question_key:string;value:unknown}
  const name=({pain_location:'Pain location',pain_score:'Pain score',chills:'Chills',breathless:'Breathlessness',temperature_f:'Temperature (°F)',last_bp:'Last blood pressure',last_sugar:'Last blood sugar',phlegm:'Phlegm',frequency_per_day:'Frequency per day',measured:'Measured'} as Record<string,string>)[follow.question_key]||'Follow-up'
  const answer=typeof follow.value==='boolean'?(follow.value?'Yes':'No'):typeof follow.value==='object'&&follow.value!==null?Object.entries(follow.value).map(([k,v])=>k+': '+v).join(', '):String(follow.value)
  return name+': '+answer
 }
 if(typeof value==='object')return Object.entries(value as Record<string,unknown>).map(([k,v])=>`${k.replaceAll('_',' ')}: ${typeof v==='object'?JSON.stringify(v):String(v)}`).join('; ')
 return ''
}
function medicineContent(record:DoctorRecord){
 const f=record.fields.medicines
 if(!accepted(f)||!Array.isArray(f!.value))return []
 return (f!.value as {name?:string|null;strength?:string|null;purpose?:string|null}[]).map(m=>{
  const known=typeof m.name==='string'&&Boolean(m.name.trim())
  const candidate=record.medicines.find(v=>norm(v.name||'')===norm(m.name||'')&&norm(v.strength||'')===norm(m.strength||''))
  return {text:known?m.name+(m.strength?' '+m.strength:''):(m.purpose?m.purpose+' medicine':'Medicine')+' (name unknown)',confirmed:candidate?.status==='confirmed',unknown:!known}
 })
}
export function applicability(record:DoctorRecord){
 const c=complaint(record.fields.complaint),reason=text(record.fields.visit_reason)
 const explicit=accepted(record.fields.current_symptoms)&&Array.isArray(record.fields.current_symptoms.value)&&record.fields.current_symptoms.value.length===0
 const denied=Boolean(c&&c.symptoms.length===0&&/no (?:current )?symptoms|asymptomatic|no complaints/i.test(c.summary))
 const positive=Boolean(c?.symptoms.length)
 const routine=Boolean(record.flow?.routine_visit||(!positive&&routinePattern.test(reason+' '+(c?.summary||''))))
 return {routine,noSymptoms:!positive&&(explicit||denied||Boolean(routine&&c&&c.symptoms.length===0)),notApplicable:!positive&&Boolean(record.flow?.duration_not_applicable||routine||explicit||denied)}
}
export function buildDoctorSummary(record:DoctorRecord){
 const stoppedEarly=record.status==='red_flag'&&record.intake_complete!==true
 const askedQuestions=new Set(record.answers.map(answer=>answer.question))
 const questionFields:Record<string,string[]>={P0:['token'],P1:['age','sex'],P2:['complaint','visit_reason','current_symptoms','red_flag_symptoms'],P3:['duration_days','duration_hours'],P4:['red_flag_symptoms'],P5:['medicines'],P6:['allergies'],P7:['conditions'],R1:['confirmed','correction'],F:['follow_up']}
 if(stoppedEarly){
  const allowed=new Set([...askedQuestions].flatMap(q=>questionFields[q]||[]))
  record={...record,fields:Object.fromEntries(Object.entries(record.fields).filter(([key])=>allowed.has(key))),medicines:askedQuestions.has('P5')?record.medicines:[]}
 }
 const earlyStopNote=stoppedEarly?'Intake stopped early after a red flag; remaining questions not asked.':''
 const notAsked=stoppedEarly?Object.entries({P0:'Token',P1:'Age and sex',P2:'Complaint',P3:'Duration',F:'Follow-ups',P4:'Safety check',P5:'Medicines',R1:'Medicine confirmation',P6:'Allergies',P7:'Conditions'}).filter(([q])=>!askedQuestions.has(q)).map(([,label])=>label):[]
 const seenAlertSymptoms=new Set<string>()
 const seenAlertAnswers=new Set<string>()
 const alertEvidence=record.answers.filter(answer=>{
  const flag=answer.red_flag as {alert?:boolean}|undefined
  return Boolean(flag?.alert||(answer.question===record.stopped_at)|| (answer.extracted.red_flag_symptoms?.status==='ok'&&Array.isArray(answer.extracted.red_flag_symptoms.value)&&answer.extracted.red_flag_symptoms.value.length))
 }).map(answer=>{
  const field=answer.extracted.red_flag_symptoms
  const flags=answer.red_flag as {keyword_flags?:string[];llm_flags?:string[]}|undefined
  const allSymptoms=[...(Array.isArray(field?.value)?field.value.filter((v):v is string=>typeof v==='string'):[]),...(flags?.keyword_flags||[]),...(flags?.llm_flags||[])]
  const symptoms=allSymptoms.filter(symptom=>{const key=norm(symptom);if(!key||seenAlertSymptoms.has(key))return false;seenAlertSymptoms.add(key);return true})
  const duplicate=allSymptoms.length>0&&!symptoms.length
  const answerKey=answer.question+'|'+answer.transcript+'|'+answer.clip_url
  const repeatedAnswer=seenAlertAnswers.has(answerKey);seenAlertAnswers.add(answerKey)
  const where=({P2:'the complaint question',P4:'the red-flag question',F:'a follow-up question'} as Record<string,string>)[answer.question]||'the '+answer.question+' question'
  return {duplicate:duplicate||repeatedAnswer,question:answer.question,detectedAt:where,title:(symptoms.length?capitalise(symptoms.join(', '))+' — reported at ':'Answer needs checking — at ')+where,symptoms,quote:field?.evidence&&answer.transcript.includes(field.evidence)?field.evidence:answer.transcript,clip:answer.clip_url}
 }).filter(e=>!e.duplicate)

 const f=record.fields,c=complaint(f.complaint),reason=clean(text(f.visit_reason)),app=applicability(record)
 const complaintText=c?complaintPhrase(c):''
 const items:Detail[]=[],attention:string[]=[],parts:string[]=[]
 const age=accepted(f.age)&&typeof f.age.value==='number'&&Number.isInteger(f.age.value)&&f.age.value>=0&&f.age.value<=110?f.age.value:null
 const sex=text(f.sex),person=sex==='male'?'man':sex==='female'?'woman':sex==='other'?'person':'patient'
 const intro=age!==null?`${age}-year-old ${person}`:sex&&sex!=='unknown'?person[0].toUpperCase()+person.slice(1):'Patient'
 const purpose=reason.replace(/^here for\s+/i,'')
 const purposeWithArticle=/^(?:routine|regular|follow[ -]?up|bp|blood pressure|diabetes|sugar)\b/i.test(purpose)?'a '+purpose:purpose
 parts.push(sentence(intro+(purpose?', here for '+purposeWithArticle:'')))
 function add(key:string,label:string,content:string,...sources:(Field|undefined)[]){if(content)items.push({key,label,text:content,evidence:evidence(...sources)})}
 const same=Boolean(reason&&c&&norm(reason)===norm(c.summary))
 if(same)add('visit','Visit reason / complaint',reason,f.visit_reason,f.complaint)
 else{
  add('visit_reason','Visit reason',reason,f.visit_reason)
  if(app.noSymptoms)add('complaint','Symptoms','No current symptoms',f.current_symptoms,f.complaint)
  else if(c)add('complaint','Complaint',complaintText,f.complaint)
 }
 let duration=''
 if(!app.notApplicable){
  if(accepted(f.duration_hours)&&typeof f.duration_hours.value==='number'&&f.duration_hours.value>0)duration=f.duration_hours.value+' hours'
  else if(accepted(f.duration_days)&&typeof f.duration_days.value==='number'&&f.duration_days.value>=0)duration=f.duration_days.value===0?'same-day onset':f.duration_days.value+' '+(f.duration_days.value===1?'day':'days')
  add('duration','Duration',duration,f.duration_days,f.duration_hours)
 }
 if(app.noSymptoms)parts.push('No current symptoms reported.')
 else if(c&&!same){const alreadyTimed=/\b(?:since|for|from)\s+/i.test(complaintText);parts.push(sentence(complaintText+(!alreadyTimed&&duration?' — '+(duration==='same-day onset'?'since today':'for '+duration):'')))}
 const followups=record.answers.filter(a=>a.question==='F'&&accepted(a.extracted.follow_up))
 if(followups.length){
  const output=followups.map(a=>format(a.extracted.follow_up)).filter(Boolean)
  add('followups','Follow-ups',output.join('; '),...followups.map(a=>a.extracted.follow_up))
 }else if(!app.notApplicable)add('follow_up','Follow-ups',format(f.follow_up),f.follow_up)
 const medicines=medicineContent(record)
 if(medicines.length){
  const content=medicines.map(m=>m.text+(m.confirmed?' (confirmed)':m.unknown?'':' (unconfirmed)')).join(', ')
  items.push({key:'medicines',label:'Medicines',text:content,medicines,evidence:evidence(f.medicines)})
  parts.push(sentence('Medicines: '+content))
 }else if(accepted(f.medicines)&&Array.isArray(f.medicines.value)&&f.medicines.value.length===0&&record.medicines.length===0){add('medicines','Medicines','None reported',f.medicines);parts.push('No medicines reported.')}
 for(const [key,title] of [['allergies','Allergies'],['conditions','Conditions']]){
  const content=format(f[key]);add(key,title,content,f[key])
  if(content==='None reported')parts.push(key==='allergies'?'No allergies reported.':'No known conditions reported.')
  else if(content)parts.push(sentence(title+': '+content))
 }
 const asked=new Set(record.answers.map(a=>a.question))
 const complete=record.status==='ready'
 const expected=new Set<string>()
 const mapping:Record<string,string[]>={P0:['token'],P1:['age','sex'],P2:['complaint'],P3:['duration_days'],P4:['red_flag_symptoms'],P5:['medicines'],P6:['allergies'],P7:['conditions'],R1:['confirmed'],F:['follow_up']}
 for(const [q,keys] of Object.entries(mapping))if(asked.has(q)||(complete&&q!=='F'))for(const key of keys)expected.add(key)
 if(app.notApplicable)expected.delete('duration_days')
 if(reason&&app.routine)expected.delete('complaint')
 if(app.noSymptoms)expected.delete('complaint')
 if(!record.medicines.length&&!asked.has('R1'))expected.delete('confirmed')
 for(const key of expected){
  const field=f[key]
  if(field?.status==='declined')attention.push(`${labels[key]}: patient declined to answer`)
  else if(!accepted(field)||field?.value==='unknown')attention.push(`${labels[key]}: ${field?.status==='question'?'patient asked for clarification':field?.value==='unknown'?'patient does not know':field?.status==='unclear'?'unclear':'not recorded'}`)
 }
 for(const field of Object.keys(f))if(f[field]?.status==='declined'&&!expected.has(field))attention.push(`${labels[field]||field.replaceAll('_',' ')}: patient declined to answer`)
 const unknowns=new Set<string>()
 for(const med of medicines)if(med.unknown)unknowns.add(med.text)
 for(const med of record.medicines)if(!med.name||med.status==='unknown_name_with_purpose'||med.status==='unclear')unknowns.add(med.display)
 for(const name of unknowns)attention.push('Medicine needs identification: '+name)
 for(const answer of record.answers){
  if(answer.question!=='R1')continue
  const corrected=answer.extracted.confirmed?.status==='ok'&&answer.extracted.confirmed.value===false
  const correction=accepted(answer.extracted.correction)?String(answer.extracted.correction.value):''
  if(corrected||correction)attention.push(correction?'Patient corrected medicine read-back: '+correction:answer.source==='button'?'Patient corrected medicine read-back'+(accepted(f.confirmed)&&f.confirmed.value===true?' (final list confirmed).':'.'):'Patient corrected medicine read-back: '+answer.transcript)
 }
 const notApplicable:string[]=[]
 if(app.notApplicable){
  const entries=['duration',...(!asked.has('F')?['follow-ups']:[])]
  const wasAsked=asked.has('P3')
  notApplicable.push(`${wasAsked?'Not applicable':'Not asked'} (${app.routine?'routine visit':'no current symptoms'}): ${entries.join(', ')}`)
 }else if(complete&&!asked.has('F')&&!accepted(f.follow_up))notApplicable.push('Not asked: follow-ups')
 const glance=parts.join(' ')
 const attentionUnique=[...new Set(attention)]
 const flag=record.red_flag as Session['red_flag']&{keyword_flags?:string[];llm_flags?:string[];positive_alert?:boolean}
 const positive=Boolean(flag.positive_alert||flag.keyword_flags?.length||flag.llm_flags?.length||record.status==='red_flag'||flag.status==='alert')
 const severity=record.status==='red_flag'?'red':flag.alert?(positive?'red':'amber'):null
 const copy=[severity?(severity==='red'?'RED FLAG — staff review required':'NEEDS CHECK — verify with reception'):'',...alertEvidence.flatMap(e=>[e.symptoms.length?'Red-flag symptoms: '+e.symptoms.join(', '):'',`Evidence: “${e.quote}”`]),`Token: ${accepted(f.token)?String(f.token.value):'not recorded'}`,'At a glance',glance,'',...items.flatMap(item=>[`${item.label}: ${item.text}`,...item.evidence.map(e=>`Evidence: “${e.quote}”`)]),...(attentionUnique.length?['','Needs attention',...attentionUnique.map(a=>'- '+a)]:[]),...notApplicable,...(earlyStopNote?[earlyStopNote,'Not asked: '+notAsked.join(', ')]:[]),'','AI-collected intake. Verify with the patient.'].filter((s,i,a)=>s||a[i-1]).join('\n')
 return {stoppedEarly,earlyStopNote,notAsked,alertEvidence,glance,items,attention:attentionUnique,notApplicable,copy,severity,age,sex,reason:reason||c?.summary||'',noSymptoms:app.noSymptoms}
}
export function queueReason(record:DoctorRecord){const model=buildDoctorSummary(record);return clean(model.reason||'Reason not recorded').split(/\s+/).slice(0,4).join(' ')}
export function timeSince(created:string,now=Date.now()){const seconds=Math.max(0,Math.floor((now-Date.parse(created))/1000));if(!Number.isFinite(seconds))return '';if(seconds<60)return 'Just now';if(seconds<3600)return Math.floor(seconds/60)+'m ago';if(seconds<86400)return Math.floor(seconds/3600)+'h ago';return Math.floor(seconds/86400)+'d ago'}
export type { Medicine, Answer }

/** Completed recorded live intakes and urgent partial live intakes are visible. */
export function isCompletedIntake(record:DoctorRecord){
 if(record.mock)return false
 if(record.status==='red_flag')return true
 if(record.status!=='ready')return false
 const required=['P0','P1','P2','P4','P5','P6','P7']
 if(!record.flow?.duration_not_applicable)required.push('P3')
 return required.every(q=>record.answers.some(a=>a.question===q&&a.source==='audio'&&!a.synthetic_mock&&Boolean(a.clip_url)&&Boolean(a.transcript?.trim())))
   &&record.answers.some(a=>a.question==='R1')
}

export function compareQueueRecords(a:DoctorRecord,b:DoctorRecord){return Number(b.status==='red_flag')-Number(a.status==='red_flag')||Date.parse(b.created_at)-Date.parse(a.created_at)}
