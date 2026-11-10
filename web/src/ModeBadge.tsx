import { useLanguage } from './language'
import { useEffect, useState } from 'react'
export type Runtime={mock:boolean;real_calls_enabled:boolean;live_session_id?:string|null}
export default function ModeBadge({mock}:{mock?:boolean}){
  const [runtime,setRuntime]=useState<Runtime|null>(null)
  useEffect(()=>{if(mock!==undefined)return;let active=true;fetch('/api/health').then(r=>{if(!r.ok)throw new Error();return r.json()}).then(body=>{if(active)setRuntime(body)}).catch(()=>{if(active)setRuntime(null)});return ()=>{active=false}},[mock])
  const value=mock??runtime?.mock
  const debug=new URLSearchParams(location.search).get('debug')==='1'
  const {t}=useLanguage()
  if(!debug&&value!==true)return null
  return <span className={`mode-badge ${value===false?'mode-live':'mode-mock'}`} role="status" aria-label={value===undefined?'App mode unavailable':value?'MOCK mode':'LIVE mode'}><span/>{debug?(value===undefined?'MODE UNAVAILABLE':value?'MOCK':'LIVE'):t('Mock mode — sample data')}</span>
}
export function TranscriptBadge({mock}:{mock:boolean}){const {t}=useLanguage();const debug=new URLSearchParams(location.search).get('debug')==='1';if(!mock&&!debug)return null;return <span className={`transcript-mode-badge ${mock?'mock-transcript':'live-transcript'}`}>{debug?(mock?'MOCK':'LIVE'):t('Mock mode — sample data')}</span>}
