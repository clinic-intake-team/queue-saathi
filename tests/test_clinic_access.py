import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api import main,clinic_access


class ClinicAccessTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        for context in [patch.object(clinic_access,'SECRET',Path(folder.name)/'secret'),patch.dict(os.environ,{'CLINIC_PIN':'4567'}),patch.object(main,'STORE',Path(folder.name)/'sessions'),patch('requests.sessions.Session.request',side_effect=AssertionError('No providers'))]:
            context.start();self.addCleanup(context.stop)
        self.client=TestClient(main.app)

    def test_pin_gate_and_persistent_token(self):
        self.assertEqual(self.client.get('/sessions').status_code,401)
        self.assertEqual(self.client.get('/doctor/access').status_code,401)
        self.assertEqual(self.client.post('/doctor/unlock',json={'pin':'1234'}).status_code,401)
        result=self.client.post('/doctor/unlock',json={'pin':'4567'});self.assertEqual(result.status_code,200)
        token=result.json()['token'];self.assertNotIn('4567',token)
        header={'Authorization':'Bearer '+token}
        self.assertEqual(self.client.get('/doctor/access',headers=header).status_code,200)
        self.assertEqual(self.client.get('/sessions',headers=header).json(),[])
        self.assertEqual(self.client.post('/doctor/unlock',json={'pin':'4567'}).json()['token'],token)
        with patch.dict(os.environ,{'CLINIC_PIN':'9876'}):
            self.assertEqual(self.client.get('/doctor/access',headers=header).status_code,401)
        self.assertEqual(self.client.get('/doctor/access').status_code,401)

    def test_demo_default_and_invalid_configuration(self):
        with patch.dict(os.environ):
            os.environ.pop('CLINIC_PIN',None)
            self.assertEqual(self.client.post('/doctor/unlock',json={'pin':'1234'}).status_code,200)
        with patch.dict(os.environ,{'CLINIC_PIN':'abc'}):
            self.assertEqual(self.client.post('/doctor/unlock',json={'pin':'1234'}).status_code,503)
