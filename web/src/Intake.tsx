import { useCallback, useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { Activity, ArrowLeft, ArrowRight, Check, CheckCircle2, CircleHelp, Clock3, Headphones, LoaderCircle, Mic, RotateCcw, ShieldAlert, ShieldCheck, Square, Volume2, X } from 'lucide-react'
import { APIError, request, sampleSession, sampleWav, screens } from './intake-api'
import type { Screen, Session } from './intake-api'
import './intake.css'
import ModeBadge, { TranscriptBadge } from './ModeBadge'
import type { Runtime } from './ModeBadge'
import KioskHeader from './KioskHeader'
import { LanguageControls, LanguageSegments, SiteLanguage, LanguageText, languageNames, useLanguage } from './language'
import type { Language } from './language'

type Mode='question'|'recording'|'transcript'|'readback'|'alert'|'done'|'busy'
const STORAGE='queuesaathi.mock.session.v1'
function destination(s:Session):Mode{return s.status==='ready'?'done':s.red_flag.alert?'alert':s.question.id==='R1'?'readback':'question'}
function initialMode(screen:Screen):Mode{return screen==='red-flag'||screen==='needs-check'?'alert':screen==='unclear'?'question':screen}
const calmBars=Array.from({length:35},(_,i)=>8+Math.abs(Math.sin(i*1.7))*24)

function IntakeFlow({onKioskReset}:{onKioskReset:()=>void}){
  const kiosk=new URLSearchParams(location.search).get('kiosk')==='1'
  const [resetSeconds,setResetSeconds]=useState(15)
  const {uiLanguage,questionLanguage,setQuestionLanguage,t,prompts}=useLanguage()
  const [changingLanguage,setChangingLanguage]=useState(false)
  const params=new URLSearchParams(location.search)
  const screen=params.get('screen') as Screen|null
  const preview=Boolean(screen&&screens.includes(screen))
  const scenario=params.get('scenario')||'normal'
  const [session,setSession]=useState<Session|null>(()=>preview?sampleSession(screen!):null)
  const [mode,setMode]=useState<Mode>(()=>preview?initialMode(screen!):'busy')
  const [feedback,setFeedback]=useState(()=>preview&&screen==='transcript'?'Kal raat se gale mein kharaash aur halki khaansi hai.':'')
  const [error,setError]=useState('')
  const [notice,setNotice]=useState('')
  const [waitingMic,setWaitingMic]=useState(false)
  const [elapsed,setElapsed]=useState(preview&&screen==='recording'?7:0)
  const [bars,setBars]=useState(calmBars)
  const [audioHint,setAudioHint]=useState('')
  const [bootAttempt,setBootAttempt]=useState(0)
  const reduced=useReducedMotion()
  const storageKey=useRef(STORAGE)
  const boot=useRef<Promise<Session>|null>(null)
  const mounted=useRef(true)
  const uploadBusy=useRef(false)
  const pendingBlob=useRef<{blob:Blob;question:string}|null>(null)
  const recorder=useRef<MediaRecorder|null>(null)
  const stream=useRef<MediaStream|null>(null)
  const context=useRef<AudioContext|null>(null)
  const animation=useRef(0)
  const limit=useRef<ReturnType<typeof setTimeout>|null>(null)
  const started=useRef(0)
  const playback=useRef<HTMLAudioElement|null>(null)
  const controller=useRef<AbortController|null>(null)
  const micGeneration=useRef(0)

  function store(s:Session){try{sessionStorage.setItem(storageKey.current,JSON.stringify({id:s.id,scenario}))}catch{/* storage is optional */}}
  useEffect(()=>{
    if(preview)return
    let active=true
    if(!boot.current)boot.current=(async()=>{
      const runtime=await request<Runtime>('/health')
      storageKey.current=runtime.mock?STORAGE:'queuesaathi.live.session.v1'
      if(!runtime.mock&&!runtime.real_calls_enabled)throw new Error('Live mode awaits confirmation.')
      let saved:{id:string;scenario:string}|null=null
      try{saved=JSON.parse(sessionStorage.getItem(storageKey.current)||'null')}catch{/* ignore stale local state */}
      if(saved&&saved.scenario===scenario&&!params.has('new')&&!kiosk){
        try{const restored=await request<Session>('/session/'+saved.id);if(!runtime.mock||restored.status==='in_progress')return restored}catch(e){if(!(e instanceof APIError&&(e.status===404||e.status===403)))throw e}
      }
      const created=await request<Session>('/session/start?scenario='+encodeURIComponent(scenario)+'&fresh='+String(params.has('new')||kiosk)+'&question_language='+questionLanguage+'&ui_language='+uiLanguage,{method:'POST'});if(params.has('new')){const clean=new URL(location.href);clean.searchParams.delete('new');history.replaceState(null,'',clean.pathname+clean.search+clean.hash)}return created
    })()
    boot.current.then(s=>{if(active){store(s);setSession(s);setQuestionLanguage(s.question_language||'hinglish');setMode(destination(s))}}).catch((e)=>{if(active){setError(e instanceof APIError?e.message:'The session could not connect. Check the app mode and connection, then try again.');setMode('question')}})
    return ()=>{active=false}
    // Boot once per mounted flow; StrictMode shares the in-flight start request.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[bootAttempt])

  useEffect(()=>{
    if(!kiosk||(mode!=='done'&&mode!=='alert'))return
    const seconds=mode==='alert'?30:15
    setResetSeconds(seconds)
    const interval=setInterval(()=>setResetSeconds(n=>Math.max(0,n-1)),1000)
    const timeout=setTimeout(onKioskReset,seconds*1000)
    return ()=>{clearInterval(interval);clearTimeout(timeout)}
  },[kiosk,mode,onKioskReset])

  const release=useCallback(()=>{
    if(limit.current)clearTimeout(limit.current)
    cancelAnimationFrame(animation.current)
    stream.current?.getTracks().forEach(track=>track.stop());stream.current=null
    if(context.current&&context.current.state!=='closed')void context.current.close()
    context.current=null
  },[])
  useEffect(()=>{mounted.current=true;return ()=>{mounted.current=false;micGeneration.current++;if(recorder.current){recorder.current.onstop=null;if(recorder.current.state==='recording')recorder.current.stop()}release();playback.current?.pause();controller.current?.abort()}},[release])
  useEffect(()=>{if(mode!=='recording'||preview)return;const interval=setInterval(()=>setElapsed(Math.floor((Date.now()-started.current)/1000)),250);return ()=>clearInterval(interval)},[mode,preview])
  const replay=useCallback(()=>{
    playback.current?.pause()
    if(!session?.question.audio_url){
      if(session&&!session.mock&&!preview){void request<Session['question']>('/session/'+session.id+'/question-audio',{method:'POST'}).then(question=>setSession(current=>current?{...current,question}:current)).catch(()=>setAudioHint(t('Question audio is unavailable. You can read the question and try Replay again.')))}
      else setAudioHint(t('This sample screen has no recorded audio.'));return
    }
    const audio=new Audio('/api'+session.question.audio_url);playback.current=audio
    if(session.question.audio_followup_url)audio.onended=()=>{const next=new Audio('/api'+session.question.audio_followup_url);playback.current=next;void next.play().catch(()=>setAudioHint(t('Tap Replay to hear the question.')))}
    void audio.play().then(()=>setAudioHint(session.mock?'Silent audio placeholder in this mock demo.':'Question audio: Timbre v3.0.')).catch(()=>setAudioHint(session.mock?'Tap Replay to play the silent demo question.':'Tap Replay to hear the question.'))
  },[session?.question.audio_url,session?.question.audio_followup_url])
  useEffect(()=>{if(session?.question.audio_url&&mode!=='transcript'&&mode!=='busy'&&mode!=='recording')replay();return ()=>{playback.current?.pause()}},[session?.question.text,mode,replay])
  useEffect(()=>{const timer=setTimeout(()=>{if(session&&mode!=='busy')document.getElementById('intake-heading')?.focus()},220);return ()=>clearTimeout(timer)},[mode,session?.question.text])

  async function upload(blob:Blob,questionId=session?.question.id,sample=false){
    if(!session||uploadBusy.current||!questionId)return
    uploadBusy.current=true;setError('');setMode('busy');pendingBlob.current={blob,question:questionId}
    const form=new FormData();form.append('audio',blob,blob.type.includes('wav')?'sample.wav':blob.type.includes('mp4')?'answer.m4a':'answer.webm');form.append('question_id',questionId);form.append('sample_answer',String(sample))
    controller.current=new AbortController()
    try{
      const result=await request<Session>('/session/'+session.id+'/answer',{method:'POST',body:form,signal:controller.current.signal})
      if(!mounted.current)return
      pendingBlob.current=null;store(result);setSession(result);setFeedback(result.transcript||'')
      setMode(result.red_flag.alert?destination(result):'transcript')
    }catch(e){if(mounted.current){
      if(e instanceof APIError&&e.status===409){try{const current=await request<Session>('/session/'+session.id);setSession(current);setMode(destination(current));pendingBlob.current=null;setNotice(t('This answer was already saved. We have restored your place.'))}catch{setMode('question');setError(t('Please reload to restore your saved place.'))}}
      else{setMode(session.question.id==='R1'?'readback':'question');setError(e instanceof APIError?e.message:'Your answer could not be saved. You can retry the upload without recording again.')}
    }}finally{uploadBusy.current=false}
  }

  async function startRecording(){
    if(waitingMic||uploadBusy.current||changingLanguage)return
    setError('');setNotice('')
    if(preview){setMode('recording');setElapsed(7);return}
    if(!session)return
    if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder){setError(t('Recording is unavailable in this browser. Please try Chrome with microphone access.'));return}
    setWaitingMic(true);const generation=++micGeneration.current
    try{
      const mic=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true}})
      if(!mounted.current||generation!==micGeneration.current){mic.getTracks().forEach(t=>t.stop());return}
      stream.current=mic
      const mime=['audio/webm;codecs=opus','audio/mp4','audio/webm'].find(t=>MediaRecorder.isTypeSupported(t))
      const rec=new MediaRecorder(mic,mime?{mimeType:mime}:undefined);recorder.current=rec
      const chunks:BlobPart[]=[]
      rec.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)}
      rec.onerror=()=>{rec.onstop=null;release();setMode('question');setError(t('The microphone stopped unexpectedly. Please try again.'))}
      rec.onstop=()=>{release();if(!mounted.current)return;const blob=new Blob(chunks,{type:rec.mimeType||'audio/webm'});if(blob.size)void upload(blob);else{setMode('question');setError(t('No audio was recorded. Please try again.'))}}
      try{
        const audioContext=new AudioContext();context.current=audioContext;void audioContext.resume()
        const analyser=audioContext.createAnalyser();analyser.fftSize=128;audioContext.createMediaStreamSource(mic).connect(analyser)
        const values=new Uint8Array(analyser.frequencyBinCount);let last=0
        const draw=(time:number)=>{if(time-last>80){analyser.getByteTimeDomainData(values);setBars(Array.from({length:35},(_,i)=>Math.max(4,Math.min(48,Math.abs(values[(i*2)%values.length]-128)*2.6+4))));last=time}animation.current=requestAnimationFrame(draw)}
        animation.current=requestAnimationFrame(draw)
      }catch{/* Recording still works if an analyser is unavailable. */}
      rec.start(200);started.current=Date.now();setElapsed(0);setMode('recording')
      limit.current=setTimeout(()=>{if(rec.state==='recording')rec.stop()},45000)
    }catch(e){release();setError(e instanceof DOMException&&e.name==='NotAllowedError'?'Microphone access was not allowed. Enable it in your browser to record.':'We could not find a working microphone. Please check your microphone settings.')}
    finally{if(mounted.current)setWaitingMic(false)}
  }
  function stopRecording(){if(preview){setFeedback('Kal raat se gale mein kharaash aur halki khaansi hai.');setMode('transcript');return}if(recorder.current?.state==='recording'){setMode('busy');recorder.current.stop()}}
  async function confirm(action:'confirm'|'correct'){
    if(!session||uploadBusy.current)return
    if(preview){if(action==='correct'){setSession(sampleSession('question'));setMode('question');setNotice(t('Zaroor. Dawai ka naam phir se bataiye.'))}else{setSession(sampleSession('done'));setMode('done')}return}
    uploadBusy.current=true;setMode('busy');setError('')
    try{const result=await request<Session>('/session/'+session.id+'/medicine-confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action})});if(mounted.current){store(result);setSession(result);setMode(destination(result));if(action==='correct')setNotice(t('Zaroor. Dawai ka naam phir se bataiye.'))}}catch{if(mounted.current){setMode('readback');setError(t('Your choice could not be saved. Please try again.'))}}finally{uploadBusy.current=false}
  }
  async function recordAgain(){
    if(!session||uploadBusy.current)return
    if(preview){setSession(sampleSession('question'));setFeedback('');setMode('question');return}
    uploadBusy.current=true;setError('')
    try{
      const restored=await request<Session>('/session/'+session.id+'/redo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({answer_count:session.answers.length})})
      if(mounted.current){store(restored);setSession(restored);setFeedback('');setNotice(t('Zaroor. Isi sawaal ka jawab phir se record karein.'));setMode('question')}
    }catch{if(mounted.current)setError(t('We could not reopen that question. Please try again.'))}
    finally{uploadBusy.current=false}
  }
  async function changeQuestionLanguage(language:Language){
    if(preview){setQuestionLanguage(language);return}
    if(!session||uploadBusy.current||mode==='recording')return
    setChangingLanguage(true);setError('');playback.current?.pause()
    try{const updated=await request<Session>('/session/'+session.id+'/language',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question_language:language,ui_language:uiLanguage})});store(updated);setSession(updated);setQuestionLanguage(language);setAudioHint('')}
    catch{setError(t('Question language could not be changed. Please try again.'))}
    finally{setChangingLanguage(false)}
  }
  function next(){setFeedback('');setNotice('');if(preview){setSession(sampleSession('question'));setMode('question')}else if(session)setMode(destination(session))}
  function useSample(){if(preview){setFeedback('Kal raat se gale mein kharaash aur halki khaansi hai.');setMode('transcript')}else if(session?.mock)void upload(sampleWav(),session.question.id,true)}
  const isAlert=mode==='alert'
  const amber=session?.status==='needs_check'
  const question=preview&&session&&prompts[questionLanguage]?.[session.question.id]?{...session.question,text:prompts[questionLanguage][session.question.id]}:session?.question
  const token=session?.fields.token?.value
  const step=question?.step||1
  return <div className={`intake-shell ${isAlert?(amber?'intake-amber':'intake-red'):''}`}>
    {kiosk?<KioskHeader onExit={onKioskReset}/>:<header className="intake-header"><a className="logo" href="/" aria-label="QueueSaathi home"><span className="logo-mark"><Activity size={23}/></span><span>Queue<span className="logo-light">Saathi</span><span className="logo-dot">.</span></span></a><ModeBadge mock={session?.mock}/><a className="intake-exit" href="/" aria-label="Exit intake"><span>{t('Exit')}</span><X size={17}/></a></header>}
    <main className="patient-main" aria-busy={mode==='busy'}><LanguageControls compact disabled={mode==='recording'||mode==='busy'||waitingMic||changingLanguage||Boolean(pendingBlob.current)} onQuestionChange={language=>void changeQuestionLanguage(language)}/>
      {(preview||session?.mock||params.get('debug')==='1')&&<div className="patient-demo"><span className="demo-dot"/>{preview||session?.mock?t('Mock mode — sample data'):'LIVE'}{preview&&!kiosk&&<a href="/intake?new=1">{t('Try full flow')}<ArrowRight size={12}/></a>}</div>}
      {mode!=='done'&&!isAlert&&<div className="patient-progress"><div><span>{t('APNI BAAT, APNE SHABDON MEIN')}</span><span>{step} of {question?.total_steps||9}</span></div><div className="progress-track" role="progressbar" aria-label="Intake progress" aria-valuemin={0} aria-valuemax={question?.total_steps||9} aria-valuenow={step}><div style={{width:`${step/(question?.total_steps||9)*100}%`}}/></div></div>}
      {error&&<div role="alert" className="patient-error"><CircleHelp size={19}/><div><p>{error}</p>{pendingBlob.current&&<button onClick={()=>{const pending=pendingBlob.current;if(pending)void upload(pending.blob,pending.question)}}>{t('Retry upload')}<RotateCcw size={14}/></button>}{!session&&<button onClick={()=>{setError('');setMode('busy');boot.current=null;setBootAttempt(n=>n+1)}}>{t('Try again')}<RotateCcw size={14}/></button>}</div></div>}
      {notice&&<div className="patient-notice" role="status"><CheckCircle2 size={17}/>{notice}</div>}
      <AnimatePresence mode="wait"><motion.div key={mode==='question'?question?.text:mode} initial={reduced?false:{opacity:0,y:8}} animate={{opacity:1,y:0}} exit={reduced?undefined:{opacity:0}} transition={{duration:.18}}>
        {mode==='busy'&&<div className="patient-card busy-card" role="status"><span className="busy-orbit"><LoaderCircle size={32}/></span><h1 id="intake-heading" tabIndex={-1}>{session?t('Ek pal… aapki baat jod rahe hain.'):t('Aapka intake shuru ho raha hai.')}</h1><p>{session?t('Please wait while your answer is saved.'):t('Getting your first question ready.')}</p></div>}
        {(mode==='question'||mode==='recording')&&session&&<section className="patient-card question-card"><div className="patient-section-label"><Headphones size={15}/>{session.retry?t('EK BAAR PHIR'):t('HUM SUN RAHE HAIN')}</div><h1 id="intake-heading" tabIndex={-1}>{question?.text}</h1><button className="replay-button" onClick={replay}><Volume2 size={15}/>{preview?t('Question audio preview'):t('Replay question')}<span>{languageNames[session.question_language||questionLanguage]}</span></button>{!session.mock&&!question?.audio_url&&<p className="patient-audio-status" role="status">{t('Question audio is not cached in this language yet.')}</p>}<p className="patient-question-help">{t('Aaram se bataiye. Hindi, English, ya dono mein.')}</p><div className={`mic-area ${mode==='recording'?'is-recording':''}`}><div className="mic-halo"/><button className="big-mic" aria-label={mode==='recording'?t('Stop recording'):t('Start recording')} onClick={mode==='recording'?stopRecording:()=>void startRecording()} disabled={waitingMic||changingLanguage}>{waitingMic?<LoaderCircle className="spin" size={37}/>:mode==='recording'?<Square size={29} fill="currentColor"/>:<Mic size={38} strokeWidth={1.6}/>}</button></div><div className="mic-instruction" aria-live="polite">{waitingMic?t('Microphone ki permission dijiye'):mode==='recording'?t('Bolte rahiye. Rokne ke liye tap karein.'):t('Bolne ke liye mic par tap karein.')}</div>{mode==='recording'?<><div className={`voice-wave ${preview?'simulated-wave':''}`} aria-hidden="true">{bars.map((height,i)=><span key={i} style={{height,animationDelay:`${i*.075}s`}}/>)}</div><div className="recording-timer"><span/><span>{String(Math.floor(elapsed/60)).padStart(2,'0')}:{String(elapsed%60).padStart(2,'0')}</span><span>{preview?t('Simulated recording · mic is off'):t('Recording · 45 sec maximum')}</span></div></>:<><div className="idle-wave" aria-hidden="true">{calmBars.slice(0,23).map((height,i)=><span key={i} style={{height:height*.25}}/>)}</div>{session.mock&&<button className="sample-answer" onClick={useSample}>{t('Use a sample answer')}<ArrowRight size={14}/></button>}</>}</section>}
        {mode==='transcript'&&<section className="patient-card transcript-card"><div className="patient-section-label"><CheckCircle2 size={17}/>{t('AAPKI BAAT')}</div><TranscriptBadge mock={session?.mock??true}/><h1 id="intake-heading" tabIndex={-1}>{t('Maine suna:')}</h1><div className="heard-quote"><span className="quote-mark" aria-hidden="true">“</span><p>{feedback}</p></div>{session?.retry?<div className="gentle-reask"><CircleHelp size={18}/><p>{t('Koi baat nahi. Ek baar phir poochte hain.')}</p></div>:<p className="patient-secondary">{t('Aapki baat note kar li hai. Agle sawaal par chalein?')}</p>}<button className="button button-primary patient-primary" onClick={next}>{session?.retry?t('Phir se bataiye'):session?.status==='ready'?t('Pura karein'):t('Agla sawaal')}<ArrowRight size={17}/></button><button className="button button-ghost record-again-button" onClick={()=>void recordAgain()}><ArrowLeft size={16}/>{t('Record again / Dobara record karein')}</button></section>}
        {mode==='readback'&&<section className="patient-card readback-card"><div className="patient-section-label"><ShieldCheck size={17}/>{t('EK BAAR PAKKA KAR LEIN')}</div><h1 id="intake-heading" tabIndex={-1}>{t('Maine yeh dawai suni.')}<br/>{t('Kya yeh sahi hai?')}</h1><p className="patient-secondary">{t('Naam yaad nahi hai? Koi baat nahi. Hum use saaf likhenge.')}</p><div className="readback-chips">{session?.medicines.length?session.medicines.map((medicine,i)=><span key={i} className={`readback-chip ${medicine.name?'':'unknown'}`}><span>{medicine.display}</span><small>{medicine.name?t('Please confirm'):t('Naam maloom nahi')}</small></span>):<span className="readback-chip">{t('Koi dawai nahi batayi')}</span>}</div><button className="replay-button" onClick={replay}><Volume2 size={16}/>{t('Read-back dobara suniye')}</button><div className="readback-actions"><button className="button button-primary" onClick={()=>void confirm('confirm')}><Check size={17}/>{t('Haan, sahi hai')}</button><button className="button button-ghost" onClick={()=>void confirm('correct')}><RotateCcw size={15}/>{t('Nahi, badalna hai')}</button></div><div className="voice-confirm"><span>{t('Ya bolkar bataiye')}</span><button onClick={()=>void startRecording()} disabled={waitingMic||changingLanguage}><Mic size={17}/>{waitingMic?t('Waiting for microphone…'):t('Voice se confirm karein')}</button></div>{session?.mock&&<button className="sample-answer" onClick={useSample}>{t('Use a sample voice answer')}<ArrowRight size={14}/></button>}</section>}
        {isAlert&&<section className={`patient-card alert-card ${amber?'amber':'red'}`} role="alert"><span className="alert-orbit"><ShieldAlert size={38}/></span><div className="patient-section-label">{amber?t('EK BAAR CHECK KARNA ZAROORI HAI'):t('RECEPTION KO ABHI BATAYEIN')}</div><h1 id="intake-heading" tabIndex={-1}>{amber?t('Aapki baat ko ek baar check karna hai.'):t('Yeh zaroori lag raha hai.')}</h1><p className="alert-message">{amber?t('Kripya reception par baat kar lijiye, taaki aapki jaankari sahi samajh sakein.'):t('Kripya abhi reception par bataiye.')}</p><p className="alert-detail">{amber?t('Is jawab ko hum pakka nahi samajh paaye.'):t('Aapne jo bataya, use staff ko pehle dekhna chahiye.')}</p><button className="button alert-replay" onClick={replay}><Volume2 size={17}/>{t('Message dobara suniye')}</button><button className="button button-primary patient-primary" onClick={onKioskReset}>{t('Theek hai')}</button>{kiosk&&<p className="kiosk-reset">Next patient in {resetSeconds} seconds.</p>}{!kiosk&&<a className="alert-home" href="/"><ArrowLeft size={15}/>{t('Back to home')}</a>}</section>}
        {mode==='done'&&<section className="patient-card done-card"><span className="done-orbit"><Check size={36}/></span><div className="patient-section-label">{t('AAPKI BAAT NOTE HO GAYI')}</div><h1 id="intake-heading" tabIndex={-1}>{t('Shukriya!')}</h1><p className="done-message">{t('Aapki jaankari doctor tak')}<br/>{t('pahunch gayi hai.')}</p><div className="token-card"><span>{t('AAPKA TOKEN')}</span><strong>{typeof token==='number'?token:'—'}</strong><span><Clock3 size={14}/>{t('Apni baari ka intezaar kijiye.')}</span></div><p className="done-disclaimer">{preview?t('Illustrative completion screen.'):session?.mock?t('This is a mock session saved in the local demo queue.'):t('Your live intake has been saved for the doctor.')}</p>{kiosk?<p className="kiosk-reset" role="status">Next patient in {resetSeconds} seconds.</p>:<><a className="button button-primary patient-primary" href="/">{t('Back to QueueSaathi')}<ArrowRight size={16}/></a>{session?.mock?<a className="restart-link" href="/intake?new=1">{t('Start another mock intake')}</a>:<a className="restart-link" href={'/doctor?session='+session?.id}>{t('Open final doctor record')}</a>}</>}</section>}
      </motion.div></AnimatePresence>
      <div className="patient-footnote"><ShieldCheck size={14}/><span>{preview?t('Fictional sample screen. No recording is started automatically.'):session?.mock?t('This demo uses fixed sample answers, not a transcription of your recording.'):t('Your spoken answers are transcribed and validated. You can re-record if something is wrong.')}</span></div>
      <p className="silent-audio-note" aria-live="polite">{audioHint||(session?.mock?t('Question audio is silent in this mock demo.'):t('Questions and medicine read-back use Timbre v3.0.'))}</p>
      <p className="patient-disclaimer">{t('Collects information only. Does not diagnose.')}</p>
    </main>
  </div>
}


export default function Intake(){
 const {uiLanguage,setUiLanguage,setQuestionLanguage,t}=useLanguage()
 const preview=screens.includes(new URLSearchParams(location.search).get('screen') as Screen)
 const [started,setStarted]=useState(preview)
 const choice=uiLanguage
 const [questions,setQuestions]=useState<Language>(uiLanguage)
 const [more,setMore]=useState(false)
 const [playing,setPlaying]=useState<Language|null>(null)
 const [audioError,setAudioError]=useState('')
 const audio=useRef<HTMLAudioElement|null>(null)
 useEffect(()=>()=>audio.current?.pause(),[])
 useEffect(()=>{if(!started)setQuestions(uiLanguage)},[uiLanguage,started])
 function choose(l:Language){setUiLanguage(l);setQuestions(l)}
 function play(l:Language){audio.current?.pause();setAudioError('');if(playing===l){setPlaying(null);return}const clip=new Audio('/api/prompts/P1.wav?language='+l);audio.current=clip;setPlaying(l);clip.onended=()=>setPlaying(null);void clip.play().catch(()=>{setPlaying(null);setAudioError('Voice preview could not play. Please try again.')})}
 const kiosk=new URLSearchParams(location.search).get('kiosk')==='1'
 const resetKiosk=useCallback(()=>{audio.current?.pause();try{sessionStorage.removeItem(STORAGE);sessionStorage.removeItem('queuesaathi.live.session.v1')}catch{}history.replaceState(null,'',new URLSearchParams(location.search).get('kiosk')==='1'?'/intake?kiosk=1&new=1':'/intake?new=1');setUiLanguage('hinglish');setQuestions('hinglish');setMore(false);setStarted(false)},[])
 if(started)return <IntakeFlow onKioskReset={resetKiosk}/>
 const options:{id:Language;title:string;description:string;example:string}[]=[{id:'hinglish',title:'Hinglish',description:'Hindi + English mix',example:'Aapki umar kitni hai?'},{id:'hi',title:'हिंदी',description:'Hindi',example:'आपकी उम्र कितनी है?'},{id:'en',title:'English',description:'English',example:'How old are you?'}]
 return <div className="intake-shell">{kiosk?<KioskHeader onExit={resetKiosk}/>:<header className="intake-header"><a className="logo" href="/"><span className="logo-mark"><Activity size={23}/></span>QueueSaathi.</a><SiteLanguage/><a className="intake-exit" href="/">{t('Exit')} <X size={17}/></a></header>}<main className="language-start"><span className="eyebrow"><LanguageText text="AAPKI BHASHA, AAPKA AARAAM"/></span><h1><LanguageText text="Kis bhasha mein baat karein?"/></h1><p><LanguageText text="Jis bhasha mein aaram ho, chuniye. Hindi aur English mix kar sakte hain."/></p><fieldset className="voice-language-cards"><legend className="sr-only">Choose intake language</legend>{options.map(o=><div className={'voice-language-card '+(choice===o.id?'selected':'')} key={o.id}><label><input type="radio" name="intake-language" value={o.id} checked={choice===o.id} onChange={()=>choose(o.id)}/><span className="voice-card-top"><Headphones size={25}/>{o.id==='hinglish'&&<span className="recommended"><LanguageText text="Recommended"/></span>}{choice===o.id&&<CheckCircle2 size={21} className="choice-check"/>}</span><strong lang={o.id==='hi'?'hi':undefined}>{o.title}</strong><span>{o.description}</span><em lang={o.id==='hi'?'hi':undefined}>“{o.example}”</em></label><button type="button" className="voice-preview" aria-label={t(playing===o.id?'Awaaz rokein':'Awaaz suniye')+' — '+o.title} aria-pressed={playing===o.id} onClick={()=>play(o.id)}><Volume2 size={16}/><LanguageText text={playing===o.id?'Awaaz rokein':'Awaaz suniye'}/></button></div>)}</fieldset>{audioError&&<p role="status">{audioError}</p>}<div className="intake-start-row"><button className="button button-primary language-start-button" disabled={!choice} onClick={()=>{audio.current?.pause();setUiLanguage(choice);setQuestionLanguage(questions);setStarted(true)}}><LanguageText text="Shuru karein"/> <ArrowRight size={17}/></button></div><div className="intake-more-row"><button className="more-languages" aria-expanded={more} aria-controls="question-language-options" onClick={()=>setMore(!more)}><LanguageText text="Sawaal alag bhasha mein chahiye? Aur options"/></button>{more&&<div id="question-language-options"><p>{t('Question language')}</p><LanguageSegments value={questions} onChange={setQuestions}/></div>}</div></main></div>
}
