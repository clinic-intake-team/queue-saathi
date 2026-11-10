import {useEffect,useState} from 'react'
import type {ReactNode} from 'react'
import {LockKeyhole} from 'lucide-react'
import {request} from './intake-api'
import {STAFF_KEY,storedToken,forgetClinic,staffRequest} from './staff-api'
let currentToken=''
export function clinicRequest<T>(path:string){return staffRequest<T>(path,currentToken)}
export default function DoctorGate({children}:{children:(lock:()=>void)=>ReactNode}){
 const [unlocked,setUnlocked]=useState(false),[checking,setChecking]=useState(true),[pin,setPin]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false)
 useEffect(()=>{let active=true;const token=storedToken();if(!token){setChecking(false);return}staffRequest('/doctor/access',token).then(()=>{if(active){currentToken=token;setUnlocked(true)}}).catch(()=>{forgetClinic()}).finally(()=>{if(active)setChecking(false)});return ()=>{active=false}},[])
 function lock(){forgetClinic();currentToken='';setUnlocked(false);setPin('');setError('')}
 async function unlock(event:React.FormEvent){event.preventDefault();setBusy(true);setError('');try{const result=await request<{token:string}>('/doctor/unlock',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin})});currentToken=result.token;try{localStorage.setItem(STAFF_KEY,result.token)}catch{/* unlock still works until page reload */}setPin('');setUnlocked(true)}catch(e){setError(e instanceof Error?e.message:'Could not unlock. Please try again.')}finally{setBusy(false)}}
 if(checking)return <main className="container preview-main" role="status">Checking clinic access…</main>
 if(unlocked)return children(lock)
 return <main className="container preview-main"><form className="glass-card clinic-pin" onSubmit={e=>void unlock(e)}><LockKeyhole size={28}/><h1>Doctor view</h1><p>Enter your 4-digit clinic PIN.</p><label htmlFor="clinic-pin">Clinic PIN</label><input id="clinic-pin" type="password" inputMode="numeric" autoComplete="off" pattern="[0-9]{4}" maxLength={4} value={pin} onChange={e=>setPin(e.target.value.replace(/\D/g,''))} required aria-describedby={error?'pin-error':undefined}/>{error&&<p id="pin-error" role="alert">{error}</p>}<button className="button button-primary" disabled={busy||pin.length!==4}>{busy?'Unlocking…':'Unlock Doctor view'}</button><small>This device stays unlocked until you select Lock.</small></form></main>
}
