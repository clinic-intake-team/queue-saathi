"""Groq provider with header-aware pacing. No network without explicit opt-in."""
import csv
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import math
import os
from pathlib import Path
import re
import sys
import threading
import time

from dotenv import load_dotenv
import requests

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
BASE_URL = 'https://api.groq.com/openai/v1'
_lock = threading.Lock()
_last_finished = 0.0
_rate = {}
_history = []
STATS = {'real_calls': 0, 'retries': 0}


class RateLimitError(RuntimeError):
    """Transport failure after retry budget, never invalid extraction output."""


class DailyQuotaError(RateLimitError):
    """Daily budget exhausted: checkpoint and exit rather than sleeping for hours."""
    def __init__(self, message, *, reset_at=None, quota=None, server_message=None,
                 wait_seconds=None, wait_hint=None):
        super().__init__(message)
        self.reset_at = reset_at
        self.quota = quota
        self.server_message = server_message
        self.wait_seconds = wait_seconds
        self.wait_hint = wait_hint


def _daily_quota(headers, data, *, observed_at=None):
    headers = {str(k).lower(): str(v) for k, v in headers.items()}
    error = data.get('error', {}) if isinstance(data, dict) else {}
    message = error.get('message', '') if isinstance(error, dict) else str(error)
    match = re.search(r'tokens per day|requests per day|\bTPD\b|\bRPD\b|daily (?:token|request|quota|limit)', message, re.I)
    if not match:
        return None
    quota = 'requests_per_day' if re.search(r'requests per day|\bRPD\b|daily request', message, re.I) else 'tokens_per_day'
    now = time.time() if observed_at is None else observed_at
    delays = []
    if headers.get('retry-after'):
        delays.append(_retry_delay(headers['retry-after'], 0))
    reset_header = 'x-ratelimit-reset-requests' if quota == 'requests_per_day' else 'x-ratelimit-reset-tokens-day'
    hint = re.search(r'try again in\s+([\d.]+(?:ms|s|m|h|d)(?:[\d.]+(?:ms|s|m|h|d))*)', message, re.I)
    if hint:
        delays.append(_seconds(hint[1].lower()))
    if not delays and headers.get(reset_header):
        delays.append(_seconds(headers[reset_header]))
    wait = max(delays) if delays else None
    return DailyQuotaError('Groq daily quota exhausted (' + quota + ')',
                           reset_at=now + wait if wait is not None else None, quota=quota,
                           server_message=message, wait_seconds=wait,
                           wait_hint=hint[1] if hint else headers.get('retry-after'))


def settings():
    provider = os.getenv('LLM_PROVIDER', 'groq').lower()
    if provider != 'groq':
        raise ValueError(f'Unsupported LLM_PROVIDER: {provider}')
    key = os.getenv('GROQ_API_KEY', '').strip()
    if not key:
        raise ValueError('Set GROQ_API_KEY in .env')
    return key, os.getenv('LLM_MODEL', '').strip()


def reasoning_effort(model=None):
    """GPT-OSS supports low/medium/high; other models omit this parameter."""
    value = os.getenv('LLM_REASONING_EFFORT', 'medium').strip().lower()
    if value not in {'low', 'medium', 'high'}:
        raise ValueError('LLM_REASONING_EFFORT must be low, medium or high')
    model = model if model is not None else os.getenv('LLM_MODEL', '')
    return value if model.startswith('openai/gpt-oss-') else None


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


def _seconds(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        parts = re.findall(r'(\d+(?:\.\d+)?)(ms|s|m|h|d)', str(value))
        return sum(float(n) * {'ms': .001, 's': 1, 'm': 60, 'h': 3600, 'd': 86400}[u] for n, u in parts)


def _pause(seconds, reason):
    if seconds > 2:
        print(f'Groq pacing: waiting {seconds:.1f}s ({reason})', file=sys.stderr, flush=True)
    # Short sleeps keep progress observable; never one blocking day-long sleep.
    remaining = max(0, seconds)
    while remaining:
        chunk = min(30, remaining)
        time.sleep(chunk)
        remaining -= chunk


def _load_rate(model):
    if model not in _rate:
        path = ROOT / 'logs/llm_rate_limits.json'
        saved = json.loads(path.read_text()) if path.exists() else {}
        _rate[model] = saved.get(model, {})
    return _rate[model]


def _capture_headers(response, model, data):
    state = _load_rate(model)
    headers = {str(k).lower(): str(v) for k, v in response.headers.items()
               if str(k).lower().startswith('x-ratelimit-') or str(k).lower() == 'retry-after'}
    # Groq standard headers: requests=PER DAY, tokens=PER MINUTE.
    mapping = {'x-ratelimit-limit-requests': 'requests_per_day',
               'x-ratelimit-limit-tokens': 'tokens_per_minute',
               'x-ratelimit-limit-requests-minute': 'requests_per_minute',
               'x-ratelimit-limit-requests-day': 'requests_per_day',
               'x-ratelimit-limit-tokens-day': 'tokens_per_day',
               'x-ratelimit-limit-tokens-minute': 'tokens_per_minute'}
    limits = state.setdefault('limits', {})
    for header, unit in mapping.items():
        if header in headers:
            limits[unit] = int(float(headers[header]))
    state.update(headers=headers, observed_at=time.time(), status=response.status_code)
    usage = data.get('usage', {}) if isinstance(data, dict) else {}
    if usage:
        state['last_total_tokens'] = usage.get('total_tokens', 0)
        state['last_completion_tokens'] = usage.get('completion_tokens', 0)
        samples = state.setdefault('usage_samples', [])
        samples.append(usage.get('total_tokens', 0))
        state['usage_samples'] = samples[-50:]
    path = ROOT / 'logs/llm_rate_limits.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_rate, indent=2) + '\n')
    with (ROOT / 'logs/llm_rate_headers.jsonl').open('a') as f:
        f.write(json.dumps({'time': datetime.now(timezone.utc).isoformat(), 'model': model,
                            'status': response.status_code, 'headers': headers}) + '\n')
    return state


def rate_limits():
    """Read observed limits only; never infer account quotas from public defaults."""
    _, model = settings()
    state = _load_rate(model)
    return {'model': model, **state}


def _reservation(payload, state):
    # Conservative estimate until actual usage arrives; includes JSON/reasoning output.
    chars = len(json.dumps(payload.get('messages', []), ensure_ascii=False).encode())
    return max(1, math.ceil(chars / 3) + max(512, math.ceil(state.get('last_completion_tokens', 0) * 1.25)))


def _pace(model, payload):
    state = _load_rate(model)
    limits = state.get('limits', {})
    tokens = _reservation(payload, state)
    state['last_reservation_tokens'] = tokens
    now = time.time()
    _history[:] = [h for h in _history if now - h[0] < 60]
    # Unknown RPM uses conservative local cap, not a claim about the account.
    rpm = limits.get('requests_per_minute') or int(os.getenv('GROQ_PACING_RPM', '30'))
    tpm = limits.get('tokens_per_minute')
    intervals = [1, 60 / max(1, rpm)]
    if tpm:
        intervals.append(60 * max(tokens, state.get('last_total_tokens', 0)) / (tpm * .85))
    delay = max(0, max(intervals) - (time.monotonic() - _last_finished))
    same = [h for h in _history if h[2] == model]
    if len(same) >= rpm:
        delay = max(delay, 60 - (now - same[0][0]) + .1)
    if tpm and sum(h[1] for h in same) + tokens > tpm * .9 and same:
        delay = max(delay, 60 - (now - same[0][0]) + .1)
    headers = state.get('headers', {})
    age = now - state.get('observed_at', 0)
    for kind, needed in [('tokens', tokens)]:
        remaining = headers.get('x-ratelimit-remaining-' + kind)
        reset = _seconds(headers.get('x-ratelimit-reset-' + kind))
        if remaining is not None and float(remaining) < needed and age < reset:
            delay = max(delay, reset - age + .1)
    _pause(delay, 'observed token/request budget')
    return tokens


def estimate_seconds(calls, *, tokens_per_call=None):
    state = rate_limits()
    limits = state.get('limits', {})
    samples = [v for v in state.get('usage_samples', []) if isinstance(v, (int, float)) and v > 0]
    tokens = tokens_per_call or max(state.get('last_reservation_tokens', 0),
                                    sum(samples) / len(samples) if samples else 2000)
    rpm = limits.get('requests_per_minute') or int(os.getenv('GROQ_PACING_RPM', '30'))
    tpm = limits.get('tokens_per_minute')
    seconds = calls * max(1, 60 / max(1, rpm), 60 * tokens / (tpm * .85) if tpm else 0)
    return {'calls': calls, 'tokens_per_call': round(tokens), 'seconds': round(seconds),
            'minutes': round(seconds / 60, 1), 'limits': limits,
            'rpm_pacing_cap': rpm, 'daily_limits_may_require_reset': (
                True if (calls > limits.get('requests_per_day', float('inf')) or
                         calls * tokens > limits.get('tokens_per_day', float('inf')))
                else (None if 'tokens_per_day' not in limits or 'requests_per_day' not in limits else False)),
            'unreported_limits': [k for k in ('requests_per_minute', 'tokens_per_day') if k not in limits],
            'note': 'Pacing time only; add response latency, Prisma time and any quota/reset waits.'}


def _request(method, endpoint, *, allow_real=False, max_attempts=6, **kwargs):
    global _last_finished
    if not allow_real:
        raise RuntimeError('Real LLM access requires explicit allow_real=True')
    if type(max_attempts) is not int or not 1 <= max_attempts <= 6:
        raise ValueError('max_attempts must be 1–6 (at most five retries)')
    key, model = settings()
    with _lock:
        for attempt in range(max_attempts):
            reservation = _pace(model, kwargs.get('json', {})) if endpoint != '/models' else 0
            response = None
            tokens = ''
            data = {}
            try:
                STATS['real_calls'] += 1
                response = requests.request(method, BASE_URL + endpoint,
                                            headers={'Authorization': 'Bearer ' + key},
                                            timeout=(15, 120), allow_redirects=False, **kwargs)
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        tokens = data.get('usage', {}).get('total_tokens', '')
                except ValueError:
                    pass
                _capture_headers(response, model, data)
            finally:
                _last_finished = time.monotonic()
                if endpoint != '/models':
                    _history.append((time.time(), tokens if type(tokens) is int else reservation, model))
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
            if response.status_code == 429 or 500 <= response.status_code < 600:
                if response.status_code == 429:
                    daily = _daily_quota(response.headers, data)
                    if daily:
                        raise daily
                if attempt + 1 < max_attempts:
                    STATS['retries'] += 1
                    _pause(_retry_delay(response.headers.get('retry-after'), attempt),
                           f'HTTP {response.status_code}; retry {attempt + 1}/{max_attempts - 1}')
                    continue
                if response.status_code == 429:
                    raise RateLimitError('Groq HTTP 429 after retry budget; resume later from cache')
            if not 200 <= response.status_code < 300:
                raise RuntimeError(f'Groq HTTP {response.status_code}: {response.text}')
            return response


def list_models(*, allow_real=False):
    return _request('GET', '/models', allow_real=allow_real).json()


def complete_json(messages, *, allow_real=False, max_attempts=6, raw_response_path=None):
    _, model = settings()
    if not model:
        raise ValueError('Set LLM_MODEL in .env')
    payload = {'model': model, 'messages': messages, 'temperature': 0,
               'response_format': {'type': 'json_object'}}
    effort = reasoning_effort(model)
    if effort is not None:
        payload['reasoning_effort'] = effort
    response = _request('POST', '/chat/completions', allow_real=allow_real,
                        max_attempts=max_attempts, json=payload)
    if raw_response_path is not None:
        output = Path(raw_response_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(response.text, encoding='utf-8')
    raw = response.json()
    parsed = json.loads(raw['choices'][0]['message']['content'])
    if not isinstance(parsed, dict):
        raise ValueError('LLM output must be a JSON object')
    return parsed, raw
