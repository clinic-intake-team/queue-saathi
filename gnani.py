"""Gnani clients. Offline by default; real access requires explicit script opt-in."""
import argparse
import csv
import hashlib
import io
import json
import mimetypes
import os
from pathlib import Path
import time
import wave
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
BASE = 'https://api.vachana.ai'
_REAL_SCRIPT = False


def _mock():
    if os.getenv('GNANI_MOCK', '1') != '0':
        return True
    if not _REAL_SCRIPT:
        raise RuntimeError('Real calls require an explicit script --real flag.')
    return False


def _seconds(audio):
    try:
        with wave.open(io.BytesIO(audio)) as stream:
            return stream.getnframes() / stream.getframerate()
    except (wave.Error, EOFError):
        return ''


def _post(endpoint, *, audio_seconds='', chars=0, **kwargs):
    key = os.getenv('GNANI_API_KEY', '').strip()
    if not key:
        raise RuntimeError('Set GNANI_API_KEY in .env for real calls.')
    for attempt in range(3):
        response = None
        try:
            response = requests.post(
                BASE + endpoint, headers={'X-API-Key-ID': key},
                timeout=(15, 120), allow_redirects=False, **kwargs,
            )
        finally:
            request_id = ''
            if response is not None:
                try:
                    body = response.json()
                    if isinstance(body, dict):
                        request_id = body.get('request_id', '')
                except ValueError:
                    pass
            log = ROOT / 'logs/api_calls.csv'
            log.parent.mkdir(parents=True, exist_ok=True)
            new = not log.exists() or log.stat().st_size == 0
            with log.open('a', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream)
                if new:
                    writer.writerow(['timestamp', 'endpoint', 'audio_seconds', 'chars', 'request_id', 'status'])
                writer.writerow([datetime.now(timezone.utc).isoformat(), endpoint,
                                 audio_seconds, chars, request_id,
                                 response.status_code if response is not None else 'network_error'])
        if response.status_code in (429, 500, 503) and attempt < 2:
            time.sleep(2 ** attempt)
            continue
        response.raise_for_status()
        if not 200 <= response.status_code < 300:
            raise RuntimeError(f'Unexpected HTTP status: {response.status_code}')
        return response


def stt(wav_path, keyterms=None, context=None):
    """Return Prisma JSON, preserving digits and Hindi number words verbatim."""
    mock = _mock()
    path = Path(wav_path)
    audio = path.read_bytes()
    fields = {'model': 'prisma-v3.0', 'language_code': 'hi-IN,en-IN', 'format': 'transcribe'}
    if keyterms is not None:
        fields['keyterms'] = json.dumps(keyterms, ensure_ascii=False)
    if context is not None:
        fields['previous_text'] = str(context)[-600:]
    # Separate mock and real caches so canned output can never mask real output.
    digest = hashlib.sha256(audio + json.dumps(
        {'fields': fields, 'mode': 'mock' if mock else 'real'},
        sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    cache = ROOT / 'cache/stt' / f'{digest}.json'
    if cache.exists():
        return json.loads(cache.read_text(encoding='utf-8'))
    if mock:
        name = 'with_keyterms.json' if keyterms else 'without_keyterms.json'
        result = json.loads((ROOT / 'data/mock' / name).read_text(encoding='utf-8'))
    else:
        response = _post('/stt/v3', audio_seconds=_seconds(audio), data=fields,
                         files={'audio_file': (path.name, audio, mimetypes.guess_type(path.name)[0] or 'application/octet-stream')})
        result = response.json()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def tts(text, out_path):
    """Cache WAV output; mock audio is silence, never fabricated speech."""
    mock = _mock()
    path = Path(out_path)
    marker = path.with_suffix(path.suffix + '.mock')
    if path.exists() and (mock or not marker.exists()):
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    if mock:
        with wave.open(str(path), 'wb') as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(16000)
            stream.writeframes(b'\0\0' * 16000)
        marker.write_text('Silent offline placeholder; regenerate with --real.\n')
    else:
        response = _post('/api/v1/tts/inference', chars=len(text), json={
            'text': text, 'model': 'timbre-v3.0', 'voice': 'Shivani',
            'language': 'hi-en', 'speed': 1.0,
            'audio_config': {'sample_rate': 16000, 'num_channels': 1,
                             'sample_width': 2, 'encoding': 'linear_pcm', 'container': 'wav'},
        })
        with wave.open(io.BytesIO(response.content)) as stream:
            stream.getparams()
        path.write_bytes(response.content)
        marker.unlink(missing_ok=True)
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real', action='store_true', help='Allow real calls; also requires GNANI_MOCK=0')
    parser.add_argument('audio', type=Path)
    parser.add_argument('--keyterms', nargs='*')
    args = parser.parse_args()
    _REAL_SCRIPT = args.real
    print(json.dumps(stt(args.audio, args.keyterms), ensure_ascii=False, indent=2))
