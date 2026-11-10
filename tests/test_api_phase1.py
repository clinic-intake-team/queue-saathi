"""API contract and credit-safety checks; no cloud requests."""
import tempfile
from pathlib import Path
import io
import os
import unittest
import wave
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api import main

class APITests(unittest.TestCase):
    def test_offline_session_and_rejection(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ,{'GNANI_MOCK':'1'}), patch.object(main,'STORE',Path(folder)/'sessions'), patch.object(main,'AUDIO',Path(folder)/'audio'), patch.object(main.clinic_access,'SECRET',Path(folder)/'clinic-secret'), patch('requests.post',side_effect=AssertionError('Network forbidden')):
            c=TestClient(main.app)
            s=c.post('/session/start').json()
            sid=s['id']
            self.assertEqual(c.get('/session/not-a-uuid').status_code,404)
            self.assertIn(c.post(f'/session/{sid}/answer',files={'audio':('bad.webm',b'bad')}).status_code,(422,503))
            audio=io.BytesIO()
            with wave.open(audio,'wb') as wav:
                wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000);wav.writeframes(b'\0\0'*4800)
            for _ in range(9):
                r=c.post(f'/session/{sid}/answer',files={'audio':('clip.wav',audio.getvalue())})
                self.assertEqual(r.status_code,200,r.text)
                s=r.json()
            self.assertTrue(s['done'])
            self.assertEqual(s['medicines'][0]['status'],'confirmed')
            self.assertEqual(c.post(f'/session/{sid}/answer',files={'audio':('clip.wav',audio.getvalue())}).status_code,409)
            self.assertEqual(c.get('/sessions').status_code,401)
            token=c.post('/doctor/unlock',json={'pin':os.getenv('CLINIC_PIN','1234')}).json()['token']
            queue=c.get('/sessions',headers={'Authorization':'Bearer '+token})
            self.assertEqual(queue.status_code,200)
            self.assertEqual(len(queue.json()),1)
            self.assertEqual(c.get(s['question']['audio_url']).status_code,200)
            with wave.open(str(next(main.AUDIO.glob('*.wav')))) as wav:
                self.assertEqual(wav.getframerate(),16000)
                self.assertEqual(wav.getnchannels(),1)
                self.assertEqual(wav.getsampwidth(),2)
            with patch.dict(os.environ,{'GNANI_MOCK':'0'}):
                self.assertEqual(c.post('/session/start').status_code,403)

    @unittest.skipUnless(__import__('shutil').which('ffmpeg'), 'System ffmpeg required')
    def test_browser_webm_and_stereo_wav_conversion(self):
        import subprocess
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ,{'GNANI_MOCK':'1'}), patch.object(main,'STORE',Path(folder)/'sessions'), patch.object(main,'AUDIO',Path(folder)/'audio'), patch.object(main.clinic_access,'SECRET',Path(folder)/'clinic-secret'), patch('requests.post',side_effect=AssertionError('Cloud calls forbidden')):
            c=TestClient(main.app)
            for suffix,codec in [('wav','pcm_s16le'),('webm','libopus')]:
                source=Path(folder)/('source.'+suffix)
                subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=0.3','-ar','48000','-ac','2','-c:a',codec,str(source)],check=True)
                sid=c.post('/session/start').json()['id']
                result=c.post(f'/session/{sid}/answer',files={'audio':(source.name,source.read_bytes())})
                self.assertEqual(result.status_code,200,result.text)
                target=main.AUDIO/result.json()['clip_url'].rsplit('/',1)[1]
                with wave.open(str(target)) as wav:
                    self.assertEqual((wav.getframerate(),wav.getnchannels(),wav.getsampwidth()),(16000,1,2))
                    self.assertGreater(wav.getnframes(),0)
