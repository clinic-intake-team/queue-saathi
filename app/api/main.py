"""Local-only API adapter. No pipeline prompts or evaluation rules are modified."""
import csv
import copy
import hashlib
import json
import io
import wave
import os
from pathlib import Path
import shutil
import subprocess
import threading
import uuid
from datetime import datetime, timezone

import yaml
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends
from pydantic import BaseModel
from typing import Literal
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import extract
import gnani
import meds
import redflags
import llm
import extract_v3 as live_extract
import redflags_v3 as live_flags
from extract_v3 import extract as extract_answer
from . import live, prompt_cache, languages, flow_rules, clinic_access
from .mock import response as mock_response

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / 'data/ui_sessions'
AUDIO = ROOT / 'cache/ui_audio'
PROMPTS = yaml.safe_load((ROOT / 'prompts.yaml').read_text())
ORDER = ['P0','P1','P2','P3','P4','P5','R1','P6','P7']
LOCK = threading.Lock()
app = FastAPI(title='QueueSaathi API', version='0.1.0', description='Phase 1 API. Local development only; no diagnosis.')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173','http://127.0.0.1:5173'], allow_methods=['GET','POST'], allow_headers=['Content-Type','Authorization'])

def mock_mode():
    return os.getenv('GNANI_MOCK','1') != '0'

def load(sid):
    try:
        sid = str(uuid.UUID(sid))
        return json.loads((STORE / f'{sid}.json').read_text())
    except (ValueError,FileNotFoundError):
        raise HTTPException(404,'Session not found')

def save(s):
    STORE.mkdir(parents=True,exist_ok=True)
    path = STORE / (s['id']+'.json')
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(s,ensure_ascii=False,indent=2))
    temp.replace(path)

def prompt_text(s):
    q=s['question_id']
    locale=s.get('question_language','hinglish')
    prompts=languages.prompts(locale,PROMPTS)
    text=languages.readback(s.get('medicines',[]),locale) if q=='R1' else prompts[q]
    if s.get('retry'):
        text=prompts['RP']+' '+text
    return text


def prompt_path(text,mock):
    digest=hashlib.sha256((text+str(mock)).encode()).hexdigest()
    return AUDIO/(digest+'.wav')


def question(s):
    # No read request can generate speech, including fixed cache misses.
    path=prompt_path(prompt_text(s),s['mock'])
    url=None;followup=None
    if not s['mock'] and s['question_id']!='R1':
        q=s['question_id'];locale=s.get('question_language','hinglish');texts=languages.prompts(locale,PROMPTS)
        if prompt_cache.valid(q,texts[q],locale):url='/prompts/'+q+'.wav?language='+locale
        if s.get('retry') and prompt_cache.valid('RP',texts['RP'],locale):
            followup=url;url='/prompts/RP.wav?language='+locale
    elif path.exists() and (s['mock'] or not path.with_suffix('.wav.mock').exists()):url='/audio/'+path.name
    visible=[q for q in ORDER if not (q=='P3' and s.get('flow',{}).get('duration_not_applicable'))]
    step=visible.index(s['question_id'])+1 if s['question_id'] in visible else len(visible)
    return {'id':s['question_id'],'text':prompt_text(s),'audio_url':url,'audio_followup_url':followup,
            'audio_is_silent_mock':s['mock'],'audio_error':s.get('audio_error'),
            'language':s.get('question_language','hinglish'),'step':step,'total_steps':len(visible)}


def prepare_audio(s):
    try:
        if not s['mock'] and s['question_id']!='R1':
            locale=s.get('question_language','hinglish');texts=languages.prompts(locale,PROMPTS)
            required=[s['question_id']]+(['RP'] if s.get('retry') else [])
            if not all(prompt_cache.valid(q,texts[q],locale) for q in required):
                raise RuntimeError('Fixed prompts require the explicit one-time precache step.')
        else:
            text=prompt_text(s);path=prompt_path(text,s['mock'])
            if s['mock']:gnani.tts(text,path)
            else:
                with live.provider_calls(s,purpose='medicine_readback',prompt_id='R1'):gnani.tts(text,path)
        s.pop('audio_error',None)
    except Exception:
        s['audio_error']='Question audio is unavailable. Fixed audio is cache-only; dynamic read-back can be retried with Replay.'
    save(s)


def keyterms_for(q):
    filename='medicines.txt' if q=='P5' else 'symptoms.txt' if q in {'P2','P4'} else None
    return (ROOT/'data'/filename).read_text().splitlines() if filename else None


def live_plan(language='hinglish'):
    uncached=[q for q,text in languages.prompts(language,PROMPTS).items() if not prompt_cache.valid(q,text,language)]
    return {'confirmed':live.approved(),'sequence':ORDER+['P8'],'button_confirmation':{'Prisma':8,'Groq_primary':8,'Groq_evidence_repairs_max':8,'Timbre':len(uncached)+1},
            'voice_confirmation':{'Prisma':9,'Groq_primary':9,'Groq_evidence_repairs_max':9,'Timbre':len(uncached)+1},
            'uncached_fixed_timbre_prompts':uncached,'dynamic_timbre_readbacks':1,
            'model':os.getenv('LLM_MODEL',''),'reasoning_effort':os.getenv('LLM_REASONING_EFFORT','medium'),
            'notes':['No retries, corrections, re-asks or early safety stop assumed.','Real cache hits reduce calls. Replays and record reads use cached audio.','Prisma/Timbre: up to 3 HTTP attempts per call; Groq: up to 6 per primary or evidence repair.','No model-list or other test calls are scheduled.']}


def view(s):
    return dict({key:value for key,value in s.items() if not key.startswith('_')}, question=question(s))

def convert(data,path):
    # Already canonical PCM16 WAV needs no transcoding. Browser WebM always
    # goes through ffmpeg below; never send a browser container to Prisma.
    try:
        with wave.open(io.BytesIO(data)) as wav:
            if (wav.getframerate(),wav.getnchannels(),wav.getsampwidth(),wav.getcomptype()) == (16000,1,2,'NONE'):
                frames=wav.readframes(16000*60)
                with wave.open(str(path),'wb') as output:
                    output.setnchannels(1); output.setsampwidth(2); output.setframerate(16000); output.writeframes(frames)
                return
    except (wave.Error,EOFError):
        pass
    try:
        executable = shutil.which('ffmpeg')
        if not executable:
            import imageio_ffmpeg
            executable = imageio_ffmpeg.get_ffmpeg_exe()
        source = path.with_suffix('.upload')
        source.write_bytes(data)
        try:
            subprocess.run([executable,'-nostdin','-v','error','-y','-i',str(source),'-t','60','-ac','1','-ar','16000','-c:a','pcm_s16le',str(path)],check=True,capture_output=True,timeout=30)
        finally:
            source.unlink(missing_ok=True)
    except (ImportError,OSError):
        raise HTTPException(503,'Install imageio-ffmpeg or ffmpeg to decode browser audio.')
    except (subprocess.SubprocessError,RuntimeError):
        raise HTTPException(422,'Audio could not be decoded; upload a valid recording under 60 seconds.')

@app.get('/health')
def health():
    return {'status':'ok','mock':mock_mode(),'phase':3,'real_calls_enabled':live.approved(),'live_session_id':live.current_id() if live.approved() else None}

@app.get('/languages')
def language_options():
    return {'prompts':{locale:languages.prompts(locale,PROMPTS) for locale in languages.LANGUAGES},
            'audio_cached':{locale:sum(prompt_cache.valid(q,t,locale) for q,t in languages.prompts(locale,PROMPTS).items()) for locale in languages.LANGUAGES}}


class LanguageChoice(BaseModel):
    question_language:Literal['hi','en','hinglish']
    ui_language:Literal['hi','en','hinglish']='hinglish'


@app.post('/session/{sid}/language')
def set_language(sid:str,choice:LanguageChoice):
    with LOCK:
        s=load(sid);mutable(s)
        s.update(question_language=choice.question_language,ui_language=choice.ui_language)
        save(s);prepare_audio(s)
        return view(s)


@app.get('/live/preflight')
def preflight(question_language:Literal['hi','en','hinglish']='hinglish'):
    return live_plan(question_language)


@app.post('/session/start')
def start(scenario: Literal['normal','unclear','red_flag','needs_check']='normal',fresh:bool=False,question_language:Literal['hi','en','hinglish']='hinglish',ui_language:Literal['hi','en','hinglish']='hinglish'):
    if not mock_mode() and not live.approved():
        raise HTTPException(403,'Live calls require starting the app with the explicit --live option.')
    if not mock_mode() and scenario!='normal':
        raise HTTPException(403,'Synthetic scenarios are only available in mock mode.')
    with LOCK:
        sid=str(uuid.uuid4()) if mock_mode() or fresh else live.current_id()
        if not mock_mode() and (STORE/(sid+'.json')).exists():
            existing=load(sid)
            return view(existing)
        if not mock_mode():
            if not os.getenv('GNANI_API_KEY','').strip():raise HTTPException(503,'GNANI_API_KEY is missing on the backend.')
            try:llm.settings()
            except ValueError:raise HTTPException(503,'Groq backend configuration is incomplete.')
            if not os.getenv('LLM_MODEL','').strip():raise HTTPException(503,'LLM_MODEL is missing on the backend.')
        s={'id':sid,'created_at':datetime.now(timezone.utc).isoformat(),'mock':mock_mode(),'status':'in_progress','intake_complete':False,'index':0,'question_id':'P0','answers':[],'fields':{},'medicines':[],'retry':False,'red_flag':{'alert':False,'status':'clear'},'scenario':scenario,'question_language':question_language,'ui_language':ui_language}
        save(s)
        if not s['mock']:live.remember(sid)
        prepare_audio(s)
        return view(s)


def mutable(s):
    if s['mock']!=mock_mode():
        raise HTTPException(403,'This record belongs to a different app mode. Start or resume the matching session.')
    if not s['mock'] and not live.approved():
        raise HTTPException(403,'This live session has not been approved for paid calls.')


def active(sid):
    s=load(sid)
    mutable(s)
    if s['status'] != 'in_progress':
        raise HTTPException(409,'Session already finished or interrupted.')
    return s


REDO_KEYS=('index','question_id','retry','fields','medicines','correcting_medicines','red_flag','status','flow','intake_complete','stopped_at')


def accept(s, transcript, fixture, clip=None, source='audio', details=None):
    """UI orchestration only; all clinical validation/detection stays in its modules."""
    q=s['question_id']
    s['_redo_snapshot']=copy.deepcopy({key:s[key] for key in REDO_KEYS if key in s})
    errors=list((details or {}).get('validation_errors',[]))
    if s['mock']:
        checked=(live_extract.validate(q,transcript,fixture,errors=errors) if q in {'P2','P7'} else extract.validate(q,transcript,fixture,errors=errors))
        checked,keyword_info,changes=live_flags.apply_negation(transcript,checked)
        flag=live_flags.detect(transcript,checked,question=q,validation_errors=errors,keyword_info=keyword_info)
    else:
        checked=live_extract.validate(q,transcript,fixture,errors=errors)
        checked,keyword_info,changes=live_flags.apply_negation(transcript,checked)
        flag=live_flags.detect(transcript,checked,question=q,validation_errors=errors,keyword_info=keyword_info)
    applicability=flow_rules.classify(q,transcript,checked,s['fields'])
    if flag.get('positive_alert') or flag.get('keyword_flags') or flag.get('llm_flags'):applicability=None
    if q=='P5':
        s['medicines']=meds.parse(transcript,extracted=checked)
        if not s['mock'] and not s['medicines'] and (checked.get('medicines',{}).get('value') or checked.get('medicines',{}).get('status')!='ok'):
            s['medicines']=[{'name':None,'strength':None,'purpose':None,'display':"unclear: '"+transcript+"'",'status':'unclear'}]
    if q=='R1':
        s['medicines']=meds.apply_confirmation(s['medicines'],transcript,checked)
    entry={'question':q,'transcript':transcript,'extracted':checked,'validation_errors':errors,
           'red_flag':flag,'clip_url':clip,'synthetic_mock':s['mock'],'source':source,'pipeline':details or {},'flow_annotation':applicability}
    s['answers'].append(entry)
    s['fields'].update({k:dict(v,clip_url=clip,source=source) for k,v in checked.items()})
    if applicability:
        s['flow']=applicability
        if applicability['no_current_symptoms']:
            s['fields']['current_symptoms']={'value':[],'status':'ok','evidence':applicability['symptom_denial_evidence'],'clip_url':clip,'source':'explicit_patient_statement'}
    elif q=='P2':
        s.pop('flow',None);s['fields'].pop('current_symptoms',None)
    if flag['alert']:
        s.update(status='needs_check' if flag['status']=='needs_check' else 'red_flag',question_id='RF',red_flag=flag,intake_complete=False,stopped_at=q)
        # Persist the collected answer before any alert audio/provider work.
        save(s)
    elif applicability and q in {'P2','P3'}:
        s.update(index=ORDER.index('P4'),question_id='P4',retry=False)
    elif q=='R1' and checked['confirmed']['value'] is False:
        # An explicit disagreement always returns to medicines; no silent approval.
        s.update(index=ORDER.index('P5'),question_id='P5',retry=False,correcting_medicines=True)
    elif any(v['status'] in {'unclear','question'} for k,v in checked.items() if k not in {'correction','red_flag_symptoms','visit_reason','duration_hours'}) and not s['retry']:
        s['retry']=True
    else:
        s['index']+=1
        s['retry']=False
        s['question_id']=ORDER[s['index']] if s['index']<len(ORDER) else 'P8'
        if s['question_id']=='P8':
            s['status']='ready'
            s['intake_complete']=True
    s.pop('pending_answer',None)
    save(s)
    prepare_audio(s)
    return dict(view(s),transcript=transcript,extracted=checked,validation_errors=errors,
                clip_url=clip,done=s['status']=='ready')


@app.post('/session/{sid}/answer')
def answer(sid:str,audio:UploadFile=File(...),question_id:str|None=Form(None),sample_answer:bool=Form(False)):
    data=audio.file.read(12*1024*1024+1)
    if not data or len(data)>12*1024*1024:
        raise HTTPException(413,'Upload between 1 byte and 12 MB.')
    with LOCK:
        s=active(sid)
        if question_id is not None and s['question_id']!=question_id:
            raise HTTPException(409,'This question has already moved on. Reload the session before answering again.')
        if sample_answer and not s['mock']:
            raise HTTPException(403,'Sample answers cannot be submitted to a live session.')
        AUDIO.mkdir(parents=True,exist_ok=True)
        path=AUDIO/(str(uuid.uuid4())+'.wav')
        convert(data,path)
        q=s['question_id']
        if s['mock']:
            gnani.stt(path,keyterms=keyterms_for(q),context=prompt_text(s))
            transcript,fixture=mock_response(q,scenario=s.get('scenario','normal'),retry=s['retry'],correcting=s.get('correcting_medicines',False))
            return accept(s,transcript,fixture,'/audio/'+path.name)
        details={}
        try:
            with live.provider_calls(s,purpose='answer_pipeline',prompt_id=q):
                before=gnani.STATS['cache_hits']
                raw=gnani.stt(path,keyterms=keyterms_for(q),context=prompt_text(s))
                transcript=raw.get('transcript') if isinstance(raw,dict) else None
                if not isinstance(transcript,str):raise ValueError('Prisma returned no transcript')
                details['stt_cache_hit']=gnani.STATS['cache_hits']>before
                s['pending_answer']={'question':q,'clip_url':'/audio/'+path.name,'transcript':transcript,'stt':raw}
                save(s)
                fixture=extract_answer(q,transcript,allow_real=True,details=details)
            return accept(s,transcript,fixture,'/audio/'+path.name,details=details)
        except llm.DailyQuotaError as error:
            reset=datetime.fromtimestamp(error.reset_at,timezone.utc).isoformat() if error.reset_at else 'not supplied by Groq'
            raise HTTPException(429,'Groq daily quota reached. Progress is saved; reset: '+reset)
        except HTTPException:raise
        except Exception:
            raise HTTPException(503,'The provider step did not finish. Your progress is saved. Retry this answer; available real caches will be reused.')



class MedicineChoice(BaseModel):
    action:Literal['confirm','correct']


@app.post('/session/{sid}/medicine-confirm')
def medicine_confirm(sid:str,choice:MedicineChoice):
    with LOCK:
        s=active(sid)
        if s['question_id']!='R1':
            raise HTTPException(409,'Medicine confirmation is only available after the medicine read-back.')
        confirmed=choice.action=='confirm'
        text='Haan, sahi hai.' if confirmed else 'Nahi, badalna hai.'
        fields={'confirmed':{'value':confirmed,'status':'ok','evidence':text},
                'correction':{'value':None,'status':'unclear','evidence':''}}
        return accept(s,text,fields,source='button')


class RedoAnswer(BaseModel):
    answer_count:int


@app.post('/session/{sid}/redo')
def redo(sid:str,choice:RedoAnswer):
    with LOCK:
        s=load(sid)
        mutable(s)
        if s['status'] not in {'in_progress','ready'}:
            raise HTTPException(409,'An interrupted safety alert cannot be erased by re-recording.')
        if not s['answers'] or choice.answer_count!=len(s['answers']):
            raise HTTPException(409,'Your session has moved on. Restore the current question before trying again.')
        previous=s['answers'][-1]
        if previous.get('source','audio')!='audio':
            raise HTTPException(409,'Only the last recorded answer can be recorded again.')
        snapshot=s.get('_redo_snapshot')
        if not snapshot:
            # Restore sessions recorded before the redo feature was added.
            prior=s['answers'][:-1]
            fields={};medicines=[]
            for entry in prior:
                fields.update({key:dict(value,clip_url=entry.get('clip_url'),source=entry.get('source','audio')) for key,value in entry['extracted'].items()})
                if entry['question']=='P5':medicines=meds.parse(entry['transcript'],extracted=entry['extracted'])
                if entry['question']=='R1':medicines=meds.apply_confirmation(medicines,entry['transcript'],entry['extracted'])
            retry=bool(prior and prior[-1]['question']==previous['question'] and any(v['status'] in {'unclear','question'} for v in prior[-1]['extracted'].values()))
            snapshot={'index':ORDER.index(previous['question']),'question_id':previous['question'],'retry':retry,
                      'fields':fields,'medicines':medicines,'status':'in_progress','red_flag':{'alert':False,'status':'clear'}}
            if s.get('correcting_medicines'):snapshot['correcting_medicines']=True
        s.setdefault('superseded_answers',[]).append(s['answers'].pop())
        for key in REDO_KEYS:
            if key in snapshot:s[key]=snapshot[key]
            else:s.pop(key,None)
        s.pop('_redo_snapshot',None)
        save(s)
        return view(s)


@app.get('/sessions')
def sessions(_clinic=Depends(clinic_access.require_clinic)):
    rows=[{key:value for key,value in json.loads(p.read_text()).items() if not key.startswith('_')} for p in sorted(STORE.glob('*.json'))]
    for row in rows:row.setdefault('intake_complete',row.get('status')=='ready')
    return sorted(rows,key=lambda row:(row.get('status')=='red_flag' and not row.get('mock',True),row.get('created_at','')),reverse=True)

@app.get('/session/{sid}')
def session(sid:str):
    return view(load(sid))

@app.post('/session/{sid}/question-audio')
def question_audio(sid:str):
    with LOCK:
        s=load(sid);mutable(s);prepare_audio(s)
        return question(s)


@app.get('/session/{sid}/calls')
def session_calls(sid:str,_clinic=Depends(clinic_access.require_clinic)):
    load(sid)
    return live.counts(sid)


@app.get('/prompts/{name}')
def fixed_prompt_audio(name:str,language:Literal['hi','en','hinglish']='hinglish'):
    q=name[:-4] if name.endswith('.wav') else ''
    texts=languages.prompts(language,PROMPTS)
    if q not in texts or not prompt_cache.valid(q,texts[q],language):raise HTTPException(404,'Fixed prompt is not cached.')
    return FileResponse(prompt_cache.directory(language)/name,media_type='audio/wav')


@app.get('/audio/{name}')
def audio_file(name:str):
    if not name.endswith('.wav') or any(c not in '0123456789abcdef-.wav' for c in name):
        raise HTTPException(404)
    path=AUDIO/name
    if not path.is_file():
        raise HTTPException(404)
    return FileResponse(path,media_type='audio/wav')

@app.get('/results')
def results():
    # Only aggregate summaries, never patient-level transcripts or secret files.
    output={}
    for prefix in ('setA','setB','setC'):
        for path in sorted((ROOT/'eval/results').glob(prefix+'_summary*.csv')):
            with path.open(newline='',encoding='utf-8-sig') as stream:
                output[path.stem]=list(csv.DictReader(stream))
    return {'datasets':output,'source':'eval/results/*_summary*.csv','limitations':['Small sample','Two speakers','v1 held-out; v2 development fixes']}


class ClinicUnlock(BaseModel):
    pin:str


@app.post('/doctor/unlock')
def doctor_unlock(choice:ClinicUnlock):
    import hmac
    if not hmac.compare_digest(choice.pin.encode(),clinic_access.clinic_pin().encode()):
        raise HTTPException(401,'Incorrect clinic PIN.')
    return {'token':clinic_access.device_token()}


@app.get('/doctor/access')
def doctor_access(_clinic=Depends(clinic_access.require_clinic)):
    return {'unlocked':True}
