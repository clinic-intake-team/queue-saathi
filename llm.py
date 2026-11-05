"""Small Groq provider. No network on import; callers explicitly opt in."""
import csv
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import os
from pathlib import Path
import threading
import time

from dotenv import load_dotenv
import requests

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
BASE_URL = 'https://api.groq.com/openai/v1'
_lock = threading.Lock()
_last_finished = 0.0


def settings():
    provider = os.getenv('LLM_PROVIDER', 'groq').lower()
    if provider != 'groq':
        raise ValueError(f'Unsupported LLM_PROVIDER: {provider}')
    key = os.getenv('GROQ_API_KEY', '').strip()
    if not key:
        raise ValueError('Set GROQ_API_KEY in .env')
    return key, os.getenv('LLM_MODEL', '').strip()


def _retry_delay(value, attempt):
    delay = 2 ** attempt
    if value:
        try:
            delay = max(delay, float(value))
        except ValueError:
            try:
                delay = max(delay, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
    return max(0, delay)


def _request(method, endpoint, *, allow_real=False, max_attempts=3, **kwargs):
    global _last_finished
    if not allow_real:
        raise RuntimeError('Real LLM access requires explicit allow_real=True')
    if max_attempts not in (1, 2, 3):
        raise ValueError('max_attempts must be between 1 and 3')
    key, model = settings()
    with _lock:
        for attempt in range(max_attempts):
            time.sleep(max(0, 1 - (time.monotonic() - _last_finished)))
            response = None
            tokens = ''
            try:
                response = requests.request(method, BASE_URL + endpoint,
                                            headers={'Authorization': 'Bearer ' + key},
                                            timeout=(15, 120), allow_redirects=False, **kwargs)
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        tokens = data.get('usage', {}).get('total_tokens', '')
                except ValueError:
                    pass
            finally:
                _last_finished = time.monotonic()
                path = ROOT / 'logs/llm_calls.csv'
                path.parent.mkdir(parents=True, exist_ok=True)
                new = not path.exists() or path.stat().st_size == 0
                with path.open('a', encoding='utf-8', newline='') as stream:
                    writer = csv.writer(stream)
                    if new:
                        writer.writerow(['time', 'model', 'tokens', 'status'])
                    writer.writerow([datetime.now(timezone.utc).isoformat(),
                                     model if endpoint != '/models' else '/models', tokens,
                                     response.status_code if response is not None else 'network_error'])
            if (response.status_code == 429 or 500 <= response.status_code < 600) and attempt + 1 < max_attempts:
                time.sleep(_retry_delay(response.headers.get('retry-after'), attempt))
                continue
            if not 200 <= response.status_code < 300:
                # Avoid including request headers or API keys in exceptions.
                raise RuntimeError(f'Groq HTTP {response.status_code}: {response.text}')
            return response


def list_models(*, allow_real=False):
    return _request('GET', '/models', allow_real=allow_real).json()


def complete_json(messages, *, allow_real=False, max_attempts=3, raw_response_path=None):
    _, model = settings()
    if not model:
        raise ValueError('Set LLM_MODEL in .env')
    response = _request('POST', '/chat/completions', allow_real=allow_real,
                        max_attempts=max_attempts, json={
                            'model': model, 'messages': messages, 'temperature': 0,
                            'response_format': {'type': 'json_object'},
                        })
    if raw_response_path is not None:
        output = Path(raw_response_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(response.text, encoding='utf-8')
    raw = response.json()
    parsed = json.loads(raw['choices'][0]['message']['content'])
    if not isinstance(parsed, dict):
        raise ValueError('LLM output must be a JSON object')
    return parsed, raw
