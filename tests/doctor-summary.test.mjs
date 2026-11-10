import test from 'node:test';import assert from 'node:assert/strict'
import {buildDoctorSummary,isCompletedIntake,compareQueueRecords,complaintPhrase,queueReason,timeSince} from '../web/src/doctor-summary.ts'
const f=(value,status='ok',evidence='Patient said this.')=>({value,status,evidence})
function routine(){return {id:'sample',mock:false,created_at:'2026-11-08T12:00:00Z',status:'ready',question:{id:'P8'},question_id:'P8',retry:false,fields:{token:f(18),age:f(35),sex:f('male'),visit_reason:f('routine BP check-up'),complaint:f({summary:'routine BP check-up',symptoms:[]}),current_symptoms:f([], 'ok', 'I do not have any symptoms.'),red_flag_symptoms:f([]),medicines:f([]),allergies:f('none'),conditions:f('none')},medicines:[],answers:['P0','P1','P2','P4','P5','R1','P6','P7'].map(question=>({question,transcript:'Example answer',extracted:question==='R1'?{confirmed:f(true)}:{},source:'audio'})),red_flag:{alert:false,status:'clear'},flow:{routine_visit:true,duration_not_applicable:true,no_current_symptoms:true},pipeline:{tokens:999}}}
test('routine summary uses explicit negatives and merges duplicate visit/complaint',()=>{const s=routine();s.fields.confirmed=f(true);const result=buildDoctorSummary(s);assert.match(result.glance,/35-year-old man/);assert.match(result.glance,/routine BP check-up/);assert.match(result.glance,/No current symptoms/);assert.match(result.glance,/No medicines reported/);assert.match(result.glance,/No allergies reported/);assert.match(result.glance,/No known conditions reported/);assert.equal(result.attention.length,0);assert.equal(result.items.filter(i=>i.key==='visit').length,1);assert.ok(!result.items.some(i=>i.key==='duration'));assert.deepEqual(result.notApplicable,['Not asked (routine visit): duration, follow-ups']);assert.ok(!result.copy.includes('999'));assert.match(result.copy,/Evidence: “/);assert.equal(queueReason(s),'routine BP check-up')})
test('missing/declined data never becomes a negative assertion',()=>{const s=routine();delete s.fields.allergies;s.fields.conditions=f(null,'declined');s.fields.medicines=f(null,'unclear');s.fields.confirmed=f(true);const r=buildDoctorSummary(s);assert.ok(!r.glance.includes('No allergies'));assert.ok(!r.glance.includes('No known conditions'));assert.ok(!r.glance.includes('No medicines'));assert.ok(r.attention.includes('Allergies: not recorded'));assert.ok(r.attention.includes('Conditions: patient declined to answer'));assert.ok(r.attention.includes('Medicines: unclear'));assert.ok(!r.items.some(i=>i.key==='allergies'))})
test('symptomatic visit retains duration and does not merge different content',()=>{const s=routine();delete s.flow;delete s.fields.current_symptoms;s.fields.complaint=f({summary:'Cough with fever',symptoms:['cough','fever']});s.fields.duration_days=f(3);const r=buildDoctorSummary(s);assert.match(r.glance,/Cough with fever — for 3 days/);assert.ok(r.items.some(i=>i.key==='duration'));assert.ok(r.items.some(i=>i.key==='visit_reason'));assert.ok(r.items.some(i=>i.key==='complaint'));assert.ok(!r.glance.includes('No current symptoms'))})
test('unknown medication and patient correction remain attention items',()=>{const s=routine();s.fields.medicines=f([{name:null,strength:null,purpose:'BP'}]);s.medicines=[{name:null,strength:null,purpose:'BP',display:'BP medicine (name unknown)',status:'unknown_name_with_purpose'}];s.fields.confirmed=f(true);s.answers.push({question:'R1',source:'button',transcript:'No, it is the other tablet.',extracted:{confirmed:f(false),correction:f('the other tablet')}});const r=buildDoctorSummary(s);assert.ok(r.attention.some(i=>i.includes('Medicine needs identification')));assert.ok(r.attention.some(i=>i.includes('Patient corrected medicine read-back: the other tablet')));assert.ok(!r.glance.includes('No medicines'))})
test('unasked future fields in an active intake are not missing-field alarms',()=>{const s=routine();s.status='in_progress';s.answers=[{question:'P0',transcript:'18',source:'audio',extracted:{token:f(18)}}];s.fields={token:f(18)};const r=buildDoctorSummary(s);assert.deepEqual(r.attention,[]);assert.ok(!r.glance.includes('No allergies'));assert.deepEqual(r.items,[])})
test('positive red flags take priority over concurrent needs_check',()=>{const s=routine();s.red_flag={alert:true,status:'needs_check',keyword_flags:['chest pain']};assert.equal(buildDoctorSummary(s).severity,'red');s.red_flag={alert:true,status:'needs_check'};assert.equal(buildDoctorSummary(s).severity,'amber');assert.match(buildDoctorSummary(s).copy,/NEEDS CHECK/)})
test('historical incorrectly asked duration is called not applicable, not not asked',()=>{const s=routine();s.answers.push({question:'P3',extracted:{duration_days:f(null,'unclear')}});s.fields.duration_days=f(null,'unclear');const r=buildDoctorSummary(s);assert.ok(!r.attention.some(a=>a.startsWith('Duration')));assert.equal(r.notApplicable[0],'Not applicable (routine visit): duration, follow-ups')})
test('time since intake updates without confusing time with token',()=>{assert.equal(timeSince('2026-11-08T12:00:00Z',Date.parse('2026-11-08T12:04:00Z')),'4m ago')})

test('clinical queue includes only fully recorded live intakes, with legitimate routine skips',()=>{
 const s=routine();s.answers=s.answers.map(a=>({...a,clip_url:'/clips/test.wav',synthetic_mock:false}));
 assert.equal(isCompletedIntake(s),true);
 s.mock=true;assert.equal(isCompletedIntake(s),false);s.mock=false;
 s.status='in_progress';assert.equal(isCompletedIntake(s),false);s.status='ready';
 s.answers=s.answers.filter(a=>a.question!=='P7');assert.equal(isCompletedIntake(s),false);
 s.answers.push({question:'P7',source:'audio',transcript:'None',clip_url:'/clips/test.wav'});
 delete s.flow;assert.equal(isCompletedIntake(s),false);
 s.answers.push({question:'P3',source:'audio',transcript:'Two days',clip_url:'/clips/test.wav'});
 assert.equal(isCompletedIntake(s),true);
 s.answers.find(a=>a.question==='P0').clip_url=null;assert.equal(isCompletedIntake(s),false);
})
test('urgent partial intake is visible before complete records without inventing unasked negatives',()=>{
 const s=routine();s.status='red_flag';s.intake_complete=false;s.stopped_at='P4';delete s.flow;delete s.fields.current_symptoms;
 s.fields.complaint=f({summary:'Headache',symptoms:['headache']});s.fields.duration_days=f(2)
 s.answers=['P0','P1','P2','P3'].map(question=>({question,transcript:'Example answer',source:'audio',clip_url:'/audio/recorded.wav',extracted:{}}))
 s.answers.push({question:'P4',transcript:'I have difficulty breathing.',clip_url:'/audio/safety.wav',source:'audio',extracted:{red_flag_symptoms:f(['breathlessness'],'ok','difficulty breathing')},red_flag:{alert:true,keyword_flags:['breathlessness'],llm_flags:['breathlessness']}})
 s.red_flag={alert:true,status:'alert',keyword_flags:['breathlessness']}
 assert.equal(isCompletedIntake(s),true)
 const summary=buildDoctorSummary(s)
 assert.equal(summary.severity,'red');assert.equal(summary.stoppedEarly,true)
 assert.match(summary.glance,/35-year-old man/);assert.match(summary.glance,/Headache — for 2 days/)
 assert.ok(!summary.glance.includes('No medicines'));assert.ok(!summary.glance.includes('No allergies'));assert.ok(!summary.glance.includes('No known conditions'))
 assert.ok(!summary.items.some(i=>['medicines','allergies','conditions'].includes(i.key)))
 assert.ok(summary.notAsked.includes('Medicines'));assert.ok(summary.notAsked.includes('Allergies'))
 assert.equal(summary.alertEvidence[0].quote,'difficulty breathing');assert.equal(summary.alertEvidence[0].clip,'/audio/safety.wav')
 assert.match(summary.copy,/Red-flag symptoms: breathlessness/);assert.match(summary.copy,/Not asked:/)
 s.mock=true;assert.equal(isCompletedIntake(s),false)
})

test('red-flag queue priority wins over a more recent completed patient',()=>{
 const complete=routine();complete.created_at='2099-01-01T00:00:00Z'
 const urgent={...routine(),status:'red_flag',intake_complete:false,id:'urgent'}
 assert.equal([complete,urgent].sort(compareQueueRecords)[0].id,'urgent')
})

test('complaint deduplicates shared concepts and preserves original timing',()=>{
 assert.equal(complaintPhrase({summary:'chest pain and heaviness since this morning',symptoms:['chest pain','heaviness in chest','chest pain']}),'Chest pain and heaviness since this morning')
 assert.equal(complaintPhrase({summary:'chest pain since morning',symptoms:['chest pain and heaviness']}),'Chest pain and heaviness since morning')
 assert.equal(complaintPhrase({summary:'cough',symptoms:['cough','fever']}),'Cough; fever')
})
test('red flag is deduplicated across layers and repeated answers, with source and one evidence clip',()=>{
 const s=routine();s.status='red_flag';s.intake_complete=false;s.stopped_at='P2';s.fields.age=f(60);s.fields.visit_reason=f(null);s.fields.complaint=f({summary:'chest pain and heaviness since this morning',symptoms:['chest pain','heaviness in chest']});delete s.flow
 const answer={question:'P2',transcript:'I have chest pain and heaviness since this morning.',clip_url:'/audio/safety.wav',source:'audio',extracted:{red_flag_symptoms:f(['Chest pain'],'ok','chest pain and heaviness since this morning')},red_flag:{alert:true,keyword_flags:['chest pain'],llm_flags:['Chest pain']}}
 s.answers=[{question:'P1',transcript:'I am 60',extracted:{}},answer,{...answer}]
 s.red_flag={alert:true,status:'alert',keyword_flags:['chest pain']}
 const model=buildDoctorSummary(s)
 assert.equal(model.alertEvidence.length,1)
 assert.equal(model.alertEvidence[0].title,'Chest pain — reported at the complaint question')
 assert.equal(model.alertEvidence[0].clip,'/audio/safety.wav')
 assert.equal(model.glance,'60-year-old man. Chest pain and heaviness since this morning.')
 assert.equal(model.items.find(i=>i.key==='complaint').text,'Chest pain and heaviness since this morning')
})
