import {Activity,X} from 'lucide-react'
import {SiteLanguage,useLanguage} from './language'
export default function KioskHeader({onExit}:{onExit:()=>void}){const {t}=useLanguage();return <header className="intake-header kiosk-header"><span className="logo" aria-label="QueueSaathi"><span className="logo-mark"><Activity size={23}/></span>QueueSaathi.</span><div className="kiosk-header-actions"><SiteLanguage/><button className="intake-exit" onClick={onExit}>{t('Exit')}<X size={17}/></button></div></header>}
