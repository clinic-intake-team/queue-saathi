"""Simulated real-mode P4 stop; no provider calls or actual patient data."""
import copy
from unittest.mock import patch
import unittest
import uuid
import test_api_live as support
from app.api import main,clinic_access


class RedFlagQueueTests(unittest.TestCase):
    setUp=support.LiveAPITests.setUp
    start=support.LiveAPITests.start
    answer=support.LiveAPITests.answer
    write_wav=support.LiveAPITests.write_wav

    def test_p4_red_flag_saved_before_audio_and_first_in_queue(self):
        with patch.object(clinic_access,'SECRET',self.root/'clinic-secret'):
            self.transcripts['P4']='I have difficulty breathing.'
            self.values['P4']={'red_flag_symptoms':['breathlessness']}
            s=self.start()
            ready=copy.deepcopy(main.load(s['id']));ready.update(id=str(uuid.uuid4()),status='ready',intake_complete=True,created_at='2099-01-01T00:00:00+00:00');main.save(ready)
            for _ in range(4):s=self.answer(s)
            self.assertEqual(s['question']['id'],'P4')
            before=copy.deepcopy(s['fields'])
            def saved_before_audio(session):
                persisted=main.load(session['id'])
                self.assertEqual(persisted['status'],'red_flag')
                self.assertFalse(persisted['intake_complete'])
                self.assertEqual(persisted['answers'][-1]['question'],'P4')
                self.assertEqual(persisted['fields']['red_flag_symptoms']['value'],['breathlessness'])
            with patch.object(main,'prepare_audio',side_effect=saved_before_audio):s=self.answer(s)
            self.assertEqual(s['status'],'red_flag');self.assertFalse(s['intake_complete'])
            self.assertEqual(s['stopped_at'],'P4')
            token=clinic_access.device_token()
            queue=self.client.get('/sessions',headers={'Authorization':'Bearer '+token})
            self.assertEqual(queue.status_code,200)
            first=queue.json()[0];self.assertEqual(first['id'],s['id']);self.assertEqual(first['status'],'red_flag')
            self.assertFalse(first['intake_complete'])
            for field in ['token','age','sex','complaint','duration_days']:self.assertEqual(first['fields'][field],before[field])
            self.assertNotIn('medicines',first['fields'])
            evidence=first['answers'][-1]
            self.assertEqual(evidence['transcript'],'I have difficulty breathing.')
            self.assertTrue(evidence['clip_url'])
            self.assertNotIn('_redo_snapshot',first)
