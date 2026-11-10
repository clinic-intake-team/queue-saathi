"""Patient flow: no cloud calls; confirmation must be explicit and alerts interrupt."""
import io
import os
from pathlib import Path
import tempfile
import unittest
import wave
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api import main

class PatientFlowTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        for context in [patch.dict(os.environ,{'GNANI_MOCK':'1'}),patch.object(main,'STORE',Path(self.folder.name)/'sessions'),patch.object(main,'AUDIO',Path(self.folder.name)/'audio'),patch('requests.post',side_effect=AssertionError('Cloud call forbidden'))]:
            context.start();self.addCleanup(context.stop)
        self.client=TestClient(main.app)
        output=io.BytesIO()
        with wave.open(output,'wb') as stream:
            stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(16000);stream.writeframes(b'\0\0'*3200)
        self.wav=output.getvalue()
    def start(self,scenario='normal'):
        response=self.client.post('/session/start',params={'scenario':scenario})
        self.assertEqual(response.status_code,200);return response.json()
    def answer(self,s):
        response=self.client.post(f"/session/{s['id']}/answer",files={'audio':('demo.wav',self.wav)},data={'question_id':s['question']['id']})
        self.assertEqual(response.status_code,200,response.text);return response.json()
    def test_explicit_medicine_correction_then_confirmation(self):
        s=self.start()
        self.assertEqual(self.client.post(f"/session/{s['id']}/medicine-confirm",json={'action':'confirm'}).status_code,409)
        for _ in range(6):s=self.answer(s)
        self.assertEqual(s['question']['id'],'R1')
        self.assertEqual(s['medicines'][0]['status'],'needs_confirmation')
        s=self.client.post(f"/session/{s['id']}/medicine-confirm",json={'action':'correct'}).json()
        self.assertEqual(s['question']['id'],'P5')
        s=self.answer(s)
        self.assertEqual(s['medicines'][0]['display'],'Paracetamol 500')
        s=self.client.post(f"/session/{s['id']}/medicine-confirm",json={'action':'confirm'}).json()
        self.assertEqual(s['question']['id'],'P6')
        self.assertEqual(s['medicines'][0]['status'],'confirmed')
        self.assertEqual(s['answers'][-1]['source'],'button')
        self.assertIsNone(s['answers'][-1]['clip_url'])
        s=self.answer(self.answer(s));self.assertTrue(s['done'])
        self.assertEqual(self.client.get(f"/session/{s['id']}").json()['question']['id'],'P8')
    def test_stale_question_cannot_advance_another_field(self):
        s=self.start();self.answer(s)
        response=self.client.post(f"/session/{s['id']}/answer",files={'audio':('demo.wav',self.wav)},data={'question_id':'P0'})
        self.assertEqual(response.status_code,409)
        self.assertEqual(len(self.client.get(f"/session/{s['id']}").json()['answers']),1)
    def test_unclear_reasks_then_preserves_valid_answer(self):
        s=self.answer(self.start('unclear'));s=self.answer(s)
        self.assertTrue(s['retry']);self.assertEqual(s['question']['id'],'P1')
        s=self.answer(s);self.assertFalse(s['retry']);self.assertEqual(s['fields']['age']['value'],34)
    def test_positive_and_uncertain_alerts_interrupt(self):
        for scenario,number,status in [('red_flag',3,'red_flag'),('needs_check',5,'needs_check')]:
            with self.subTest(scenario=scenario):
                s=self.start(scenario)
                for _ in range(number):s=self.answer(s)
                self.assertEqual(s['status'],status);self.assertEqual(s['question']['id'],'RF');self.assertTrue(s['red_flag']['alert'])
                self.assertEqual(self.client.post(f"/session/{s['id']}/answer",files={'audio':('demo.wav',self.wav)}).status_code,409)
    def test_records_are_read_only_in_other_modes_and_mutations_are_blocked(self):
        s=self.start()
        with patch.dict(os.environ,{'GNANI_MOCK':'0'}):
            self.assertEqual(self.client.get(f"/session/{s['id']}").status_code,200)
            self.assertEqual(self.client.post(f"/session/{s['id']}/medicine-confirm",json={'action':'confirm'}).status_code,403)
    def test_redo_replaces_answer_and_removes_its_fields(self):
        s=self.answer(self.start());sid=s['id']
        self.assertEqual(s['fields']['token']['value'],24)
        restored=self.client.post(f'/session/{sid}/redo',json={'answer_count':1}).json()
        self.assertEqual(restored['question']['id'],'P0');self.assertEqual(restored['answers'],[])
        self.assertNotIn('token',restored['fields'])
        self.assertEqual(len(restored['superseded_answers']),1)
        self.assertEqual(self.client.post(f'/session/{sid}/redo',json={'answer_count':1}).status_code,409)
        replaced=self.answer(restored)
        self.assertEqual(len(replaced['answers']),1);self.assertEqual(replaced['fields']['token']['value'],24)
    def test_redo_final_answer_and_legacy_sessions(self):
        s=self.start()
        for _ in range(9):s=self.answer(s)
        sid=s['id'];self.assertTrue(s['done'])
        restored=self.client.post(f'/session/{sid}/redo',json={'answer_count':9}).json()
        self.assertEqual(restored['status'],'in_progress');self.assertEqual(restored['question']['id'],'P7')
        self.assertNotIn('conditions',restored['fields']);self.assertEqual(restored['fields']['token']['value'],24)
        s=self.answer(restored)
        raw=main.load(sid);raw.pop('_redo_snapshot');main.save(raw)
        restored=self.client.post(f'/session/{sid}/redo',json={'answer_count':9}).json()
        self.assertEqual(restored['question']['id'],'P7');self.assertNotIn('conditions',restored['fields'])
    def test_redo_cannot_clear_safety_alert(self):
        s=self.start('red_flag')
        for _ in range(3):s=self.answer(s)
        self.assertEqual(self.client.post(f"/session/{s['id']}/redo",json={'answer_count':3}).status_code,409)
        self.assertTrue(self.client.get(f"/session/{s['id']}").json()['red_flag']['alert'])
    def test_start_fresh_always_creates_distinct_mock_session(self):
        first=self.start()
        for _ in range(9):first=self.answer(first)
        self.assertEqual(first['status'],'ready')
        for _ in range(3):
            result=self.client.post('/session/start?fresh=true').json()
            self.assertNotEqual(result['id'],first['id'])
            self.assertEqual(result['question']['id'],'P0')
            self.assertEqual(result['status'],'in_progress')
            self.assertEqual(result['answers'],[])
        self.assertEqual(self.client.get(f"/session/{first['id']}").json()['status'],'ready')

    def test_question_and_interface_languages_are_independent_and_persist(self):
        from app.api import languages
        for locale in ('hi','en','hinglish'):
            result=self.client.post('/session/start',params={'question_language':locale,'ui_language':'en','fresh':True})
            self.assertEqual(result.status_code,200);s=result.json()
            self.assertEqual(s['question_language'],locale);self.assertEqual(s['ui_language'],'en')
            self.assertEqual(s['question']['text'],languages.prompts(locale,main.PROMPTS)['P0'])
            s=self.answer(s)
            self.assertEqual(s['question']['text'],languages.prompts(locale,main.PROMPTS)['P1'])
            restored=self.client.get(f"/session/{s['id']}").json()
            self.assertEqual(restored['question_language'],locale)
        self.assertEqual(self.client.post('/session/start?question_language=unsupported').status_code,422)
        self.assertEqual(set(languages.prompts('hi',main.PROMPTS)),set(main.PROMPTS))
        self.assertEqual(set(languages.prompts('en',main.PROMPTS)),set(main.PROMPTS))
