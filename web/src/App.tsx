import { useEffect, useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Activity, ArrowDown, ArrowRight, Check, ChevronRight, FileCheck2, HeartPulse, Languages, Menu, Mic, ShieldCheck, Sparkles, X } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { landingMetrics } from './results'
import type { Metrics } from './results'
import ProductPreview from './ProductPreview'
import Intake from './Intake'
import ModeBadge from './ModeBadge'
import Doctor from './Doctor'
import ResultsPage from './ResultsPage'
import { SiteLanguage, useLanguage } from './language'

type ButtonProps = { children: React.ReactNode; href: string; variant?: 'primary' | 'white' | 'ghost'; className?: string }
function Button({children,href,variant='primary',className=''}:ButtonProps) {
  return <a className={`button button-${variant} ${className}`} href={href}>{children}</a>
}
function Logo(){return <a className="logo" href="/" aria-label="QueueSaathi home"><span className="logo-mark"><Activity size={23} strokeWidth={2}/></span><span>Queue<span className="logo-light">Saathi</span><span className="logo-dot">.</span></span></a>}
function Nav({showMode=true}:{showMode?:boolean}){
  const [open,setOpen]=useState(false)
  const {t}=useLanguage()
  return <header className="header"><div className="container nav"><Logo/><nav className="desktop-links" aria-label="Main navigation"><a href="/#how-it-works">{t('How it works')}</a><a href="/results">{t('Results')}</a><a href="/doctor">Doctor view <ChevronRight size={13}/></a></nav><div className="nav-actions"><SiteLanguage/>{showMode&&<ModeBadge/>}<Button href="/intake?new=1" variant="ghost">Start intake <ArrowUpRight/></Button><button className="menu-button" onClick={()=>setOpen(!open)} aria-label={open?'Close navigation':'Open navigation'} aria-expanded={open} aria-controls="mobile-nav">{open?<X/>:<Menu/>}</button></div></div>{open&&<nav id="mobile-nav" className="mobile-links" aria-label="Mobile navigation"><a onClick={()=>setOpen(false)} href="/#how-it-works">{t('How it works')}</a><a onClick={()=>setOpen(false)} href="/results">{t('Results')}</a><a href="/doctor">{t('Doctor view')}</a></nav>}</header>
}
function ArrowUpRight(){return <ArrowRight size={15} className="diagonal-arrow"/>}
function useMetrics(){
  const [state,setState]=useState<{data:Metrics|null;error:boolean}>({data:null,error:false})
  const [attempt,setAttempt]=useState(0)
  useEffect(()=>{
    const controller=new AbortController()
    const timeout=setTimeout(()=>controller.abort(),10000)
    fetch('/api/results',{signal:controller.signal}).then(r=>{if(!r.ok)throw new Error('Results unavailable');return r.json()}).then(body=>setState({data:landingMetrics(body.datasets),error:false})).catch(()=>{if(!controller.signal.aborted)setState({data:null,error:true});else if(!cancelled)setState({data:null,error:true})}).finally(()=>clearTimeout(timeout))
    let cancelled=false
    return ()=>{cancelled=true;clearTimeout(timeout);controller.abort()}
  },[attempt])
  return {...state,retry:()=>{setState({data:null,error:false});setAttempt(n=>n+1)}}
}
function ResultStats(){
  const {t}=useLanguage()
  const {data,error,retry}=useMetrics()
  return <section id="results" className="results-section container" aria-labelledby="results-title">
    <div className="section-eyebrow" id="results-title"><span className="tiny-line"/> TESTED WITH REAL HINGLISH RECORDINGS <span className="tiny-line"/></div>
    {error?<div className="results-error" role="status">{t('Recorded results are temporarily unavailable.')}<button onClick={retry}>{t('Try again')}<ArrowRight size={14}/></button></div>:<div className="stats-grid" aria-busy={!data}>
      <div className="stat"><div className="stat-number medicine-number">{data?<><span>{data.medicineOff}%</span><ArrowRight aria-label="improved to" size={27}/><strong>{data.medicineOn}%</strong></>:<span className="skeleton" aria-label="Loading medicine results"/>}</div><h3>{t('Medicine-name accuracy')}</h3><p>{t('With Prisma medicine keyterms')}</p><span className="data-source">{t('40 recorded clips · 2 speakers')}</span></div>
      <div className="stat"><div className="stat-number">{data?data.caught:<span className="skeleton" aria-label="Loading red flag results"/>}<span className="metric-icon green"><ShieldCheck size={21}/></span></div><h3>{t('Red flags caught')}</h3><p>{t('Every emergency case flagged')}</p><span className="data-source">{t('20 full patient sessions')}</span></div>
      <div className="stat"><div className="stat-number">{data?data.falseAlarms:<span className="skeleton" aria-label="Loading false alarm results"/>}<span className="metric-icon blue"><Activity size={21}/></span></div><h3>{t('False alarms after fixes')}</h3><p>{t('Safety with fewer interruptions')}</p><span className="data-source">{t('After fixes · see Results')}</span></div>
    </div>}
    <p className="results-caption">{t('On our recorded Hinglish test set.')}<a href="#results-notes">{t('See results context')}<ArrowRight size={12}/></a></p>
  </section>
}
const steps:{icon:LucideIcon;number:string;title:string;description:string;tag:string}[]=[
  {icon:Mic,number:'01',title:'Speak in Hinglish.',description:'Hindi, English, or a little of both. Share your symptoms and medicines in your own words.',tag:'PRISMA v3.0'},
  {icon:ShieldCheck,number:'02',title:'Checked, not guessed.',description:'Fields are validated. Red flags get an extra check. Unclear answers are kept visible.',tag:'VALIDATION + SAFETY CHECKS'},
  {icon:FileCheck2,number:'03',title:'Doctor gets a summary.',description:'Hear your medicines read back. Your doctor gets a clear summary with your words as evidence.',tag:'TIMBRE v3.0 READ-BACK'},
]
function HowItWorks(){const {t}=useLanguage();return <section id="how-it-works" className="how-section container" aria-labelledby="how-title"><div className="section-heading"><div><div className="eyebrow">{t('A LITTLE TALK. A BETTER HANDOFF.')}</div><h2 id="how-title">{t('Your words. A clearer')}{' '}<em>{t('picture.')}</em></h2></div><p>{t('Less repetition at the desk.')}<br/>{t('More context for the conversation that matters.')}</p></div><div className="steps-grid">{steps.map(({icon:Icon,...step})=><article className="glass-card step-card" key={step.number}><div className="card-top"><span className="step-icon"><Icon size={24} strokeWidth={1.6}/></span><span className="step-number">{step.number}</span></div><h3>{t(step.title)}</h3><p>{t(step.description)}</p><div className="card-tag"><span/>{step.tag}</div></article>)}</div></section>}
function Footer(){const {t}=useLanguage();return <footer className="container footer"><div className="footer-main"><Logo/><p>{t('Your history reaches the doctor before you do.')}</p><a href="/intake?new=1">{t('Start a conversation')}<ArrowUpRight/></a></div><div className="footer-bottom"><p>{t('Built on Gnani Prisma v3.0 and Timbre v3.0')}<span>·</span> Extraction: gpt-oss-120b via Groq</p><p><ShieldCheck size={13}/> Collects information only, does not diagnose.</p></div></footer>}
function Landing(){
  const reduce=useReducedMotion()
  const {t}=useLanguage()
  return <><main><section className="hero"><div className="hero-glow" aria-hidden="true"><div className="horizon haze"/><div className="horizon arc"/><div className="horizon arc-inner"/><div className="horizon bloom"/></div><motion.div className="container hero-content" initial={reduce?false:{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{duration:.65,ease:'easeOut'}}><div className="pill-badge"><Sparkles size={13}/><span>{t('New: Hinglish voice intake')}</span><ChevronRight size={13}/></div><p className="hero-hindi">{t('Doctor ko pehle se pata ho.')}</p><h1>{t('Your history, before')}<br/>{t('you')}{' '}<em>{t('walk in.')}</em></h1><p className="hero-description">{t('A few words in your language. A clearer picture for your doctor.')}<br className="desktop-break"/>{' '}{t('Voice intake that listens, checks, and brings your story together.')}</p><div className="hero-buttons"><Button href="/intake?new=1"><Mic size={17}/>{t('Start patient intake')}<ArrowRight size={16}/></Button><Button href="/doctor" variant="white">{t('Open doctor view')}<ArrowUpRight/></Button></div><div className="hero-assurances"><span><Languages size={14}/>{t('Hindi + English, naturally')}</span><span className="assurance-dot"/><span><Check size={14}/>{t('Your words stay visible')}</span></div><a className="explore-link" href="#how-it-works" aria-label="Explore how QueueSaathi works"><ArrowDown size={16}/></a></motion.div></section><ResultStats/><ProductPreview/><HowItWorks/><section id="results-notes" className="container context-section"><div className="context-icon"><HeartPulse size={23}/></div><div><h3>{t('Real recordings. Honest limits.')}</h3><p>{t('These results come from a small, two-speaker recorded test set in quiet conditions. See Results for evaluation details and development changes. An alert is a prompt for staff to check, not a diagnosis.')}</p></div><a href="#results">{t('Back to the numbers')}<ArrowUpRight/></a></section><section className="container closing-section"><div><span className="eyebrow">{t('BEFORE THE CONSULTATION BEGINS')}</span><h2>{t('Make room for the')}{' '}<em>{t('conversation.')}</em></h2><p>{t('Your history reaches the doctor before you do.')}</p></div><Button href="/intake?new=1">{t('Start patient intake')}<ArrowRight size={16}/></Button></section></main><Footer/></>
}
export default function App(){const path=window.location.pathname;return <><a className="skip-link" href="#main-content">Skip to content</a>{path!=='/intake'&&<Nav showMode={path!=='/doctor'}/>}<div id="main-content" tabIndex={-1}>{path==='/intake'?<Intake/>:path==='/doctor'?<Doctor/>:path==='/results'?<ResultsPage/>:path==='/'?<Landing/>:<main className="container preview-main"><h1>That page isn't here.</h1><Button href="/" variant="white">Back to home</Button></main>}</div></>}
