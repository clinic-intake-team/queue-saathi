import {request} from './intake-api'
export const STAFF_KEY='queuesaathi.clinic.device'
export function storedToken(){try{return localStorage.getItem(STAFF_KEY)||''}catch{return ''}}
export function forgetClinic(){try{localStorage.removeItem(STAFF_KEY)}catch{/* memory unlock still clears */}}
export function staffRequest<T>(path:string,token=storedToken()){return request<T>(path,{headers:{Authorization:'Bearer '+token}})}
