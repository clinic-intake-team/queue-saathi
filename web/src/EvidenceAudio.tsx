import {useState} from 'react'
/** Read-only playback. Metadata loading makes duration visible before pressing Play. */
export default function EvidenceAudio({clip,label}:{clip:string;label:string}){
 const [failed,setFailed]=useState(false)
 const src=clip.startsWith('/api/audio/')?clip:'/api'+clip
 return <div className="evidence-playback"><audio key={src} controls preload="metadata" src={src} aria-label={label} onLoadedMetadata={()=>setFailed(false)} onError={()=>setFailed(true)}/>{failed&&<small role="status">Recording could not be loaded. <button type="button" onClick={event=>{setFailed(false);event.currentTarget.closest('.evidence-playback')?.querySelector('audio')?.load()}}>Retry audio</button></small>}</div>
}
