"""Live wiring simulated at the provider boundary. These tests make ZERO paid calls."""
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid
import wave

import requests
from fastapi.testclient import TestClient
from app.api import main, live, prompt_cache
from contextlib import redirect_stdout

class LiveAPITests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup);self.root=Path(folder.name)
        self.sid=str(uuid.uuid4())
        contexts=[patch.object(main,'STORE',self.root/'sessions'),patch.object(main,'AUDIO',self.root/'audio'),
          patch.object(live,'CALL_LOG',self.root/'calls.csv'),patch.object(live,'POINTER',self.root/'last.txt'),patch.object(prompt_cache,'DIRECTORY',self.root/'fixed'),patch.object(prompt_cache,'MANIFEST',self.root/'fixed/manifest.json'),
          patch.dict(os.environ,{'GNANI_MOCK':'0','GNANI_UI_LIVE_APPROVED':'1','GNANI_UI_LIVE_SESSION_ID':self.sid,
            'GNANI_API_KEY':'test-only','GROQ_API_KEY':'test-only','LLM_MODEL':'openai/gpt-oss-120b'}),
          patch('requests.post',side_effect=AssertionError('Paid request forbidden')),
          patch('requests.request',side_effect=AssertionError('Paid request forbidden'))]
        for context in contexts:context.start();self.addCleanup(context.stop)
        self.client=TestClient(main.app)
        self.q='P0';self.tts=[];self.stt=[];self.groq=[]
        self.transcripts={'P0':'Mera token 31 hai.','P1':'Main 42 saal ka purush hoon.',
          'P2':'Mujhe naak band hai.','P3':'Teen din se.','P4':'Koi dikkat nahi.',
          'P5':'mein crocin le raha hu','P6':'Koi nahi.','P7':'Koi nahi.','R1':'Haan sahi hai.'}
        self.values={'P0':{'token':31},'P1':{'age':42,'sex':'male'},
          'P2':{'complaint':{'summary':'Blocked nose','symptoms':['blocked nose']},'red_flag_symptoms':[],'visit_reason':None},
          'P3':{'duration_days':3,'duration_hours':None},'P4':{'red_flag_symptoms':[]},
          'P5':{'medicines':[{'name':'Crocin','strength':None,'purpose':None}]},
          'P6':{'allergies':'none'},'P7':{'conditions':'none'},'R1':{'confirmed':True,'correction':None}}
        def tts(text,path):
            self.assertTrue(main.gnani._REAL_SCRIPT)
            path=Path(path)
            if not path.exists():self.tts.append(text);self.write_wav(path)
            return path
        def stt(path,keyterms=None,context=None):
            self.assertTrue(main.gnani._REAL_SCRIPT)
            self.stt.append((self.q,keyterms,context))
            return {'transcript':self.transcripts[self.q]}
        def extract(q,transcript,allow_real=False,details=None):
            self.assertTrue(allow_real);self.assertEqual(transcript,self.transcripts[q]);self.groq.append(q)
            if details is not None:details.update(validation_errors=[],result_cache_hit=False)
            return {k:{'value':v,'status':'ok' if v is not None else 'unclear','evidence':transcript if v is not None else ''} for k,v in self.values[q].items()}
        for context in [patch.object(main.gnani,'tts',side_effect=tts),patch.object(main.gnani,'stt',side_effect=stt),patch.object(main,'extract_answer',side_effect=extract)]:
            context.start();self.addCleanup(context.stop)
        buf=io.BytesIO()
        with wave.open(buf,'wb') as stream:
            stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(16000);stream.writeframes(b'\0\0'*3200)
        self.wav=buf.getvalue()
    def write_wav(self,path):
        path.parent.mkdir(parents=True,exist_ok=True)
        with wave.open(str(path),'wb') as stream:
            stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(16000);stream.writeframes(b'\0\0'*3200)
    def start(self):
        with redirect_stdout(io.StringIO()):prompt_cache.generate({'id':self.sid,'mock':False},main.PROMPTS)
        result=self.client.post('/session/start');self.assertEqual(result.status_code,200,result.text);return result.json()
    def answer(self,s):
        self.q=s['question']['id']
        result=self.client.post(f"/session/{s['id']}/answer",files={'audio':('recorded.wav',self.wav)},data={'question_id':self.q})
        self.assertEqual(result.status_code,200,result.text);return result.json()
    def test_real_crocin_transcript_end_to_end_and_call_plan(self):
        s=self.start();self.assertFalse(s['mock'])
        for _ in range(6):s=self.answer(s)
        self.assertEqual(s['transcript'],'mein crocin le raha hu')
        self.assertEqual(s['medicines'][0]['name'],'Crocin');self.assertIsNone(s['medicines'][0]['strength'])
        self.assertIn('Crocin',s['question']['text']);self.assertNotIn('Dolo',s['question']['text'])
        self.assertFalse(s['answers'][-1]['synthetic_mock'])
        s=self.client.post(f"/session/{s['id']}/medicine-confirm",json={'action':'confirm'}).json()
        self.assertEqual(s['medicines'][0]['status'],'confirmed')
        s=self.answer(self.answer(s));self.assertTrue(s['done'])
        self.assertEqual((len(self.stt),len(self.groq),len(self.tts)),(8,8,21))
        for q,terms,context in self.stt:
            self.assertTrue(context)
            if q=='P5':self.assertIn('Crocin',terms)
            elif q in {'P2','P4'}:self.assertIn('blood',terms)
            else:self.assertIsNone(terms)
        before=(len(self.tts),len(self.stt),len(self.groq))
        self.client.get('/sessions');self.client.get(f"/session/{self.sid}");self.client.get(f"/session/{self.sid}/calls")
        self.assertEqual(before,(len(self.tts),len(self.stt),len(self.groq)))
        self.assertEqual(self.start()['id'],self.sid);self.assertEqual(before,(len(self.tts),len(self.stt),len(self.groq)))
    def test_explicit_denial_never_reads_back_fuzzy_body_part(self):
        self.transcripts['P5']='No medicine, I only have pain in my palm'
        self.values['P5']={'medicines':[{'name':'Pan','strength':None,'purpose':None}]}
        s=self.start()
        for _ in range(6):s=self.answer(s)
        self.assertEqual(s['fields']['medicines']['value'],[])
        self.assertEqual(s['medicines'],[])
        self.assertNotIn('Pan',s['question']['text'])

    def test_no_live_calls_without_explicit_gate(self):
        with patch.dict(os.environ,{'GNANI_UI_LIVE_APPROVED':'0'}):
            self.assertEqual(self.client.post('/session/start').status_code,403)
            self.assertFalse(self.client.get('/health').json()['real_calls_enabled'])
        self.assertEqual(self.tts,[])
    def test_samples_cannot_enter_live_session(self):
        s=self.start()
        response=self.client.post(f"/session/{s['id']}/answer",files={'audio':('sample.wav',self.wav)},data={'sample_answer':'true'})
        self.assertEqual(response.status_code,403);self.assertEqual(self.stt,[])
    def test_prisma_or_groq_failure_does_not_insert_canned_answer(self):
        s=self.start()
        with patch.object(main,'extract_answer',side_effect=RuntimeError('Provider failure')):
            result=self.client.post(f"/session/{s['id']}/answer",files={'audio':('recorded.wav',self.wav)})
        self.assertEqual(result.status_code,503)
        saved=main.load(self.sid);self.assertEqual(saved['answers'],[])
        self.assertEqual(saved['pending_answer']['transcript'],self.transcripts['P0'])
    def test_existing_live_record_reads_never_generate_missing_audio(self):
        s=self.start();Path(prompt_cache.DIRECTORY/s['question']['audio_url'].rsplit('/',1)[1].split('?',1)[0]).unlink()
        before=len(self.tts)
        self.assertIsNone(self.client.get(f"/session/{self.sid}").json()['question']['audio_url'])
        self.assertEqual(len(self.tts),before)
    def test_transport_audit_identifies_every_provider_attempt(self):
        response=requests.Response();response.status_code=200
        response._content=json.dumps({'usage':{'total_tokens':17}}).encode()
        session={'id':self.sid,'mock':False}
        with patch.object(live,'_original_request',return_value=response):
            with live.provider_calls(session):
                live._request(requests.Session(),'POST','https://api.groq.com/openai/v1/chat/completions',json={'model':'test'})
        audit=live.counts(self.sid)
        self.assertEqual(audit['real_http_attempts']['Groq'],1);self.assertEqual(audit['groq_tokens'],17)
        self.assertNotIn('test-only',live.CALL_LOG.read_text())

    def test_fresh_live_starts_need_no_repeated_approval_and_keep_history(self):
        original=self.start()
        for _ in range(8):
            if original['question']['id']=='R1':
                original=self.client.post(f"/session/{original['id']}/medicine-confirm",json={'action':'confirm'}).json()
            original=self.answer(original)
        self.assertEqual(original['status'],'ready')
        before=(len(self.stt),len(self.groq),len(self.tts))
        ids={original['id']}
        for _ in range(3):
            result=self.client.post('/session/start?fresh=true')
            self.assertEqual(result.status_code,200,result.text)
            new=result.json();self.assertNotIn(new['id'],ids);ids.add(new['id'])
            self.assertEqual(new['question']['id'],'P0');self.assertEqual(new['answers'],[])
            self.assertFalse(new['mock']);self.assertEqual(live.current_id(),new['id'])
            # A session created after the original one can actually accept audio.
            self.assertEqual(self.client.post(f"/session/{new['id']}/medicine-confirm",json={'action':'confirm'}).status_code,409)
        self.assertEqual(before,(len(self.stt),len(self.groq),len(self.tts)))
        self.assertEqual(self.client.get(f"/session/{original['id']}").json()['status'],'ready')
        new=self.answer(new)
        self.assertEqual(new['question']['id'],'P1')

    def test_language_change_is_text_only_until_explicit_audio_precache(self):
        from app.api import languages
        s=self.start();before=(len(self.tts),len(self.stt),len(self.groq))
        result=self.client.post(f"/session/{s['id']}/language",json={'question_language':'en','ui_language':'hi'})
        self.assertEqual(result.status_code,200)
        s=result.json();self.assertEqual(s['question_language'],'en');self.assertTrue(s['question']['text'].startswith('Hello!'))
        self.assertIsNone(s['question']['audio_url']);self.assertEqual(before,(len(self.tts),len(self.stt),len(self.groq)))
        self.assertEqual(self.client.get('/prompts/P0.wav?language=en').status_code,404)
        self.assertEqual(self.client.get('/prompts/P0.wav?language=hinglish').status_code,200)
        self.assertEqual(languages.readback([{'name':'Crocin','strength':None}],'en'),'You mentioned: Crocin. Is that correct?')
        self.assertIn('Crocin',languages.readback([{'name':'Crocin','strength':None}],'hi'))
        s=self.answer(s);self.assertEqual(s['question_language'],'en');self.assertTrue(self.stt[-1][2].startswith('Hello!'))
    def test_fixed_audio_languages_have_isolated_caches(self):
        from app.api import languages
        self.start();original=(prompt_cache.DIRECTORY/'P0.wav').read_bytes()
        with redirect_stdout(io.StringIO()):prompt_cache.generate({'id':self.sid,'mock':False},languages.prompts('en',main.PROMPTS),only='P0',language='en')
        self.assertTrue((prompt_cache.DIRECTORY/'en/P0.wav').exists())
        self.assertEqual((prompt_cache.DIRECTORY/'P0.wav').read_bytes(),original)
        self.assertTrue(prompt_cache.valid('P0',languages.prompts('en',main.PROMPTS)['P0'],'en'))
        self.assertTrue(prompt_cache.valid('P0',main.PROMPTS['P0']))
