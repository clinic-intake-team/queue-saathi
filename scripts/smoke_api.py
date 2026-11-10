"""Run an entire synthetic session using actual curl HTTP requests."""
import os
import io
import json
from pathlib import Path
import subprocess
import tempfile
import wave
BASE=os.getenv('API_URL','http://127.0.0.1:8000')
def curl(*args):
    return json.loads(subprocess.check_output(['curl','--fail-with-body','--silent','--show-error',*args],text=True))
with tempfile.TemporaryDirectory() as folder:
    path=Path(folder)/'answer.wav'
    with wave.open(str(path),'wb') as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(16000); wav.writeframes(b'\0\0'*8000)
    s=curl('-X','POST',BASE+'/session/start')
    sid=s['id']
    for _ in range(20):
        q=s['question']['id']
        s=curl('-X','POST','-F',f'audio=@{path}',BASE+'/session/'+sid+'/answer')
        print(q,'→',s['question']['id'],s['status'])
        assert not s['validation_errors'],s['validation_errors']
        if s['done']:
            break
    assert s['done'] and len(s['answers'])==9
    assert s['medicines'][0]['status']=='confirmed'
    assert curl(BASE+'/session/'+sid)['status']=='ready'
    assert any(row['id']==sid for row in curl(BASE+'/sessions'))
    assert 'setA_summary' in curl(BASE+'/results')['datasets']
    subprocess.check_call(['curl','--fail','--silent','-o',str(Path(folder)/'prompt.wav'),BASE+s['question']['audio_url']])
    print('PASS: 9 answers, confirmed medicine, persisted ready record, queue, results and audio. Session:',sid)
