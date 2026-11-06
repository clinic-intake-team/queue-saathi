import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import extract
import llm


def response(status, headers=None, data=None):
    r = Mock(status_code=status, headers=headers or {})
    r.json.return_value = data if data is not None else {}
    r.text = json.dumps(r.json.return_value)
    return r


class NormalizationTests(unittest.TestCase):
    def test_sentinels_both_fields(self):
        for question, field in [('P6', 'allergies'), ('P7', 'conditions')]:
            for value in ['none', ['none'], ['no'], ['koi nahi'], [], 'unknown', ['unknown'], ['pata nahi'], ["don't know"]]:
                expected = 'unknown' if value in ['unknown', ['unknown'], ['pata nahi'], ["don't know"]] else 'none'
                errors = []
                result = extract.validate(question, 'answer', {field: {'value': value, 'status': 'ok', 'evidence': 'answer'}}, errors=errors)
                self.assertEqual(result[field]['value'], expected)
                self.assertFalse(errors)
            for sentinel in ['none', 'unknown', 'no', 'koi nahi', 'pata nahi', "don't know"]:
                name = 'penicillin' if question == 'P6' else 'diabetes'
                result = extract.validate(question, 'answer', {field: {'value': [sentinel, name], 'status': 'ok', 'evidence': 'answer'}})
                self.assertEqual(result[field]['value'], [name])
            result = extract.validate(question, 'answer', {field: {'value': ['none'], 'status': 'ok', 'evidence': 'invented'}})
            self.assertEqual(result[field]['status'], 'unclear')


class RateLimitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = patch.object(llm, 'ROOT', Path(self.temp.name)); self.root.start()
        self.rate = patch.object(llm, '_rate', {}); self.rate.start()
        self.history = patch.object(llm, '_history', []); self.history.start()
        self.settings = patch('llm.settings', return_value=('fake-key', 'model')); self.settings.start()

    def tearDown(self):
        self.settings.stop(); self.history.stop(); self.rate.stop(); self.root.stop(); self.temp.cleanup()

    def test_header_units_and_reset(self):
        headers = {'X-RateLimit-Limit-Requests': '1000', 'x-ratelimit-limit-tokens': '8000',
                   'x-ratelimit-remaining-tokens': '100', 'x-ratelimit-reset-tokens': '1m2.5s'}
        llm._capture_headers(response(200, headers), 'model', {})
        self.assertEqual(llm.rate_limits()['limits'], {'requests_per_day': 1000, 'tokens_per_minute': 8000})
        self.assertNotIn('requests_per_minute', llm.rate_limits()['limits'])
        self.assertEqual(llm._seconds('1m2.5s'), 62.5)
        with patch('llm._pause') as pause:
            llm._pace('model', {'messages': []})
            self.assertGreater(pause.call_args.args[0], 60)

    def test_429_retries_then_valid_output(self):
        data = {'choices': [{'message': {'content': '{"ok": true}'}}], 'usage': {'total_tokens': 200}}
        with patch('requests.request', side_effect=[response(429, {'retry-after': '7'}), response(200, data=data)]) as request, patch('llm._pause') as pause, patch('llm._pace', return_value=200):
            result, _ = llm.complete_json([], allow_real=True)
            self.assertEqual(result, {'ok': True})
            self.assertEqual(request.call_count, 2)
            self.assertTrue(any(c.args[0] >= 7 for c in pause.call_args_list))

    def test_five_retries_exhausted_is_transport_error_not_invalid_json(self):
        with patch('requests.request', return_value=response(429)) as request, patch('llm._pause'), patch('llm._pace', return_value=200):
            with self.assertRaises(llm.RateLimitError):
                llm.complete_json([], allow_real=True)
            self.assertEqual(request.call_count, 6)
        with tempfile.TemporaryDirectory() as folder, patch.object(extract, 'ROOT', Path(folder)), patch('llm.complete_json', side_effect=llm.RateLimitError('429')):
            with self.assertRaises(llm.RateLimitError): extract.extract('P0', 'token one', allow_real=True)
            self.assertFalse(list(Path(folder).rglob('*.validated_v3.json')))

    def test_daily_quota_reports_reset_without_retrying(self):
        data = {'error': {'message': 'Rate limit reached on tokens per day (TPD). Please try again in 2h3m4s.'}}
        with patch('requests.request', return_value=response(429, {'retry-after': '7384'}, data)) as request, patch('llm._pause'), patch('llm._pace', return_value=200), patch('llm.time.time', return_value=1000):
            with self.assertRaises(llm.DailyQuotaError) as caught:
                llm.complete_json([], allow_real=True)
            self.assertEqual(request.call_count, 1)
            self.assertEqual(caught.exception.quota, 'tokens_per_day')
            self.assertEqual(caught.exception.reset_at, 8384)

    def test_reasoning_effort_is_forwarded_only_for_gpt_oss(self):
        data = {'choices': [{'message': {'content': '{}'}}]}
        for effort in ['low', 'medium', 'high']:
            with patch.dict('os.environ', {'LLM_REASONING_EFFORT': effort}), patch('llm.settings', return_value=('fake', 'openai/gpt-oss-120b')), patch('llm._request', return_value=response(200, data=data)) as request:
                llm.complete_json([], allow_real=True)
                self.assertEqual(request.call_args.kwargs['json']['reasoning_effort'], effort)
        with patch.dict('os.environ', {'LLM_REASONING_EFFORT': 'low'}), patch('llm.settings', return_value=('fake', 'other-model')), patch('llm._request', return_value=response(200, data=data)) as request:
            llm.complete_json([], allow_real=True)
            self.assertNotIn('reasoning_effort', request.call_args.kwargs['json'])
        with patch.dict('os.environ', {'LLM_REASONING_EFFORT': 'invalid'}):
            with self.assertRaises(ValueError): llm.reasoning_effort('openai/gpt-oss-120b')

    def test_reasoning_effort_separates_extraction_caches(self):
        with patch('llm.settings', return_value=('fake', 'openai/gpt-oss-120b')):
            with patch.dict('os.environ', {'LLM_REASONING_EFFORT': 'low'}):
                low = extract.cache_path('P0', 'token two')
            with patch.dict('os.environ', {'LLM_REASONING_EFFORT': 'medium'}):
                medium = extract.cache_path('P0', 'token two')
            self.assertNotEqual(low, medium)

    def test_no_pre_call_daily_guard_and_minute_429_retries(self):
        data = {'choices': [{'message': {'content': '{}'}}]}
        error = {'error': {'message': 'Rate limit reached on tokens per minute (TPM).'}}
        with patch('requests.request', side_effect=[response(429, {'retry-after': '3', 'x-ratelimit-remaining-requests': '0'}, error), response(200, data=data)]) as request, patch('llm._pause'), patch('llm._pace', return_value=200):
            result, _ = llm.complete_json([], allow_real=True)
            self.assertEqual(result, {})
            self.assertEqual(request.call_count, 2)

    def test_requests_per_day_error_preserves_message_and_wait(self):
        message = 'Rate limit reached on requests per day (RPD). Please try again in 3m10s.'
        with patch('requests.request', return_value=response(429, {}, {'error': {'message': message}})) as request, patch('llm._pace', return_value=200), patch('llm.time.time', return_value=1000):
            with self.assertRaises(llm.DailyQuotaError) as caught:
                llm.complete_json([], allow_real=True)
            self.assertEqual(request.call_count, 1)
            self.assertEqual(caught.exception.server_message, message)
            self.assertEqual(caught.exception.wait_seconds, 190)
            self.assertEqual(caught.exception.reset_at, 1190)
