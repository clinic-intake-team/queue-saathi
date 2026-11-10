"""Explicitly enabled live UI sessions and per-HTTP-attempt provider audit logging."""
from contextlib import contextmanager
from contextvars import ContextVar
import csv
from datetime import datetime, timezone
import os
from pathlib import Path
import threading
import time
from urllib.parse import urlparse

import requests
import gnani

ROOT=Path(__file__).resolve().parents[2]
CALL_LOG=ROOT/'logs/ui_session_calls.csv'
POINTER=ROOT/'cache/ui_last_live_session_id.txt'
_session=ContextVar('ui_session_id',default=None)
_purpose=ContextVar('ui_call_purpose',default=('', ''))
_log_lock=threading.Lock()
_original_request=requests.sessions.Session.request


def approved():
    return os.getenv('GNANI_MOCK','1')=='0' and os.getenv('GNANI_UI_LIVE_APPROVED')=='1'


def current_id():
    return POINTER.read_text().strip() if POINTER.exists() else os.environ.get('GNANI_UI_LIVE_SESSION_ID','')


def remember(sid):
    POINTER.parent.mkdir(parents=True,exist_ok=True)
    temp=POINTER.with_suffix('.tmp');temp.write_text(sid+'\n');temp.replace(POINTER)


def _request(self,method,url,*args,**kwargs):
    sid=_session.get()
    parsed=urlparse(str(url))
    if not sid or parsed.hostname not in {'api.vachana.ai','api.groq.com'}:
        return _original_request(self,method,url,*args,**kwargs)
    response=None;start=time.monotonic();tokens=''
    payload=kwargs.get('json') or kwargs.get('data') or {}
    model=payload.get('model','') if isinstance(payload,dict) else ''
    provider='Groq' if parsed.hostname=='api.groq.com' else ('Prisma' if '/stt/' in parsed.path else 'Timbre')
    try:
        response=_original_request(self,method,url,*args,**kwargs)
        if provider=='Groq':
            try:tokens=response.json().get('usage',{}).get('total_tokens','')
            except (ValueError,AttributeError):pass
        return response
    finally:
        with _log_lock:
            CALL_LOG.parent.mkdir(parents=True,exist_ok=True)
            new=not CALL_LOG.exists() or CALL_LOG.stat().st_size==0
            with CALL_LOG.open('a',newline='',encoding='utf-8') as stream:
                writer=csv.writer(stream)
                if new:writer.writerow(['time','session_id','provider','method','endpoint','model','tokens','status','seconds','purpose','prompt_id'])
                writer.writerow([datetime.now(timezone.utc).isoformat(),sid,provider,method,parsed.path,model,tokens,
                                 response.status_code if response is not None else 'network_error',round(time.monotonic()-start,3),*_purpose.get()])


requests.sessions.Session.request=_request


@contextmanager
def provider_calls(s,*,purpose='answer_pipeline',prompt_id=''):
    if s['mock'] or not approved() :
        raise RuntimeError('Paid UI calls require the explicit live launcher.')
    token=_session.set(s['id']);meta=_purpose.set((purpose,prompt_id));old=gnani._REAL_SCRIPT;gnani._REAL_SCRIPT=True
    try:yield
    finally:gnani._REAL_SCRIPT=old;_session.reset(token);_purpose.reset(meta)


def counts(sid):
    rows=[]
    if CALL_LOG.exists():
        with CALL_LOG.open(newline='',encoding='utf-8') as stream:
            rows=[row for row in csv.DictReader(stream) if row['session_id']==sid]
    return {'real_http_attempts':{provider:sum(row['provider']==provider for row in rows) for provider in ('Prisma','Timbre','Groq')},
            'groq_tokens':sum(int(row['tokens']) for row in rows if str(row['tokens']).isdigit()),'calls':rows}
