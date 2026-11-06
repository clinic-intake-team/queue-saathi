import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import extract
import llm
from eval import resume_setB_v1 as resume


class ResumeTests(unittest.TestCase):
    def test_medium_cache_matches_original_recipe(self):
        import os
        with patch('llm.settings', return_value=('fake', 'openai/gpt-oss-120b')), patch.dict(os.environ, {'LLM_REASONING_EFFORT': 'medium'}):
            value = extract.cache_path('F', 'own answer', question_key='measured')
            payload = {'provider': 'groq', 'model': 'openai/gpt-oss-120b', 'question': 'F',
                       'transcript': 'own answer', 'prompt': extract.SYSTEM_PROMPT, 'question_key': 'measured'}
            expected = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            self.assertEqual(value.stem, expected)

    def test_all_prisma_first_then_clean_quota_stop_and_no_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / 'cache/setB_full_v1_checkpoint.json'
            checkpoint.parent.mkdir()
            checkpoint.write_text(json.dumps({'protocol_hash': 'original', 'clips': []}))
            paths = [root / 'recordings/ch_S01_P0.m4a', root / 'recordings/ch_S01_P1.m4a']
            caches = {p: root / 'cache' / (p.stem + '.json') for p in paths}
            events = []
            def stt(path, **kwargs):
                events.append('prisma:' + path.stem)
                value = {'transcript': 'own development example'}
                caches[path].write_text(json.dumps(value))
                return value
            def fake_extract(*args, **kwargs):
                events.append('groq_429')
                raise llm.DailyQuotaError('daily quota exhausted', quota='tokens_per_day', server_message='tokens per day (TPD); try again in 3m', wait_seconds=180, wait_hint='3m', reset_at=2000000000)
            with patch.object(resume, 'ROOT', root), patch.object(resume, 'verify_resume', return_value='original'), patch('gnani.stt_cache_path', side_effect=lambda p,*a,**kw:caches[p]), patch('gnani.stt', side_effect=stt) as call, patch('extract.cached_available', return_value=False), patch('extract.extract', side_effect=fake_extract), patch('requests.request', side_effect=AssertionError('No network')), patch('eval.run_setB.score_session') as score, contextlib.redirect_stdout(io.StringIO()):
                self.assertIsNone(resume.run(paths, {}, {'P0':'question', 'P1':'question'}, [], [], allow_real=True))
                self.assertEqual(events, ['prisma:ch_S01_P0', 'prisma:ch_S01_P1', 'groq_429'])
                saved = json.loads(checkpoint.read_text())
                self.assertEqual(saved['status'], 'daily_quota_stopped')
                self.assertEqual(saved['stt_ready'], 2)
                self.assertFalse((root / 'eval/results/setB_summary.csv').exists())
                score.assert_not_called()
                call.reset_mock()
                resume.run(paths, {}, {'P0':'question', 'P1':'question'}, [], [], allow_real=True)
                call.assert_not_called()
                saved = json.loads(checkpoint.read_text())
                self.assertEqual(saved['skipped_thanks_to_cache']['prisma'], 2)
