"""Explicit one-time fixed Timbre generation; runtime fixed playback is read-only."""
import hashlib
import json
from pathlib import Path
import wave
import gnani
from . import live

ROOT=Path(__file__).resolve().parents[2]
DIRECTORY=ROOT/'assets/prompts'
MANIFEST=DIRECTORY/'live_manifest.json'
VOICE={'model':'timbre-v3.0','voice':'Shivani','language':'hi-en'}
# prompts.yaml accidentally includes workflow annotations inside RP. Use the exact
# existing UI retry sentence; never synthesize annotations as patient speech.
RETRY='Maaf kijiye, theek se samajh nahi aaya. Ek baar phir bataiye?'

def texts(prompts,language='hinglish'):
    return dict(prompts,RP=RETRY) if language=='hinglish' else dict(prompts)

def directory(language='hinglish'):
    if language not in {'hinglish','hi','en'}:raise ValueError('Unsupported prompt language')
    return DIRECTORY if language=='hinglish' else DIRECTORY/language

def manifest(language='hinglish'):
    return MANIFEST if language=='hinglish' else directory(language)/'live_manifest.json'

def digest(text):return hashlib.sha256(text.encode()).hexdigest()

def valid(q,text,language='hinglish'):
    path=directory(language)/(q+'.wav')
    try:
        data=json.loads(manifest(language).read_text()).get(q,{})
        return (not path.with_suffix('.wav.mock').exists() and data.get('text_sha256')==digest(text)
                and data.get('voice')==VOICE and data.get('audio_sha256')==hashlib.sha256(path.read_bytes()).hexdigest())
    except (OSError,ValueError):return False

def generate(s,prompts,only=None,language='hinglish'):
    target=directory(language);index=manifest(language)
    target.mkdir(parents=True,exist_ok=True)
    saved=json.loads(index.read_text()) if index.exists() else {}
    selected=texts(prompts,language)
    if only is not None:
        if only not in selected:raise ValueError('Unknown fixed prompt: '+only)
        selected={only:selected[only]}
    for q,text in selected.items():
        if valid(q,text,language):
            print(f'Fixed prompt {q}: cache hit (0 Timbre calls)',flush=True);continue
        path=target/(q+'.wav')
        # Preserve an unverified existing real file before replacing it.
        if path.exists() and not path.with_suffix('.wav.mock').exists():
            backup=ROOT/'cache/ui_prompt_backups'/language/path.name
            backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(path.read_bytes())
            path.unlink()
        with live.provider_calls(s,purpose='fixed_prompt',prompt_id=q):
            gnani.tts(text,path)
        with wave.open(str(path)) as stream:
            if not stream.getnframes():raise RuntimeError('Empty fixed prompt audio: '+q)
        saved[q]={'text_sha256':digest(text),'audio_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'voice':VOICE,'session_id':s['id']}
        temp=index.with_suffix('.tmp');temp.write_text(json.dumps(saved,ensure_ascii=False,indent=2));temp.replace(index)
        print(f'Fixed prompt {q}: generated and cached',flush=True)
