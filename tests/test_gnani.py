import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

import gnani


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        fixtures = self.root / 'data/mock'
        fixtures.mkdir(parents=True)
        for source in (gnani.ROOT / 'data/mock').glob('*.json'):
            (fixtures / source.name).write_bytes(source.read_bytes())
        self.audio = self.root / 'test.wav'
        self.audio.write_bytes(b'audio fixture')
        self.patch = patch.object(gnani, 'ROOT', self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    @patch.dict(os.environ, {'GNANI_MOCK': '1'})
    @patch('gnani.requests.post', side_effect=AssertionError('network forbidden'))
    def test_mock_variants_and_cache(self, post):
        self.assertIn('2 दिन', gnani.stt(self.audio)['transcript'])
        self.assertIn('दो दिन', gnani.stt(self.audio, ['Telma'])['transcript'])
        self.assertEqual(len(list((self.root / 'cache/stt').glob('*.json'))), 2)
        gnani.tts('hello', self.root / 'prompt.wav')
        self.assertTrue((self.root / 'prompt.wav.mock').exists())
        post.assert_not_called()

    @patch.dict(os.environ, {'GNANI_MOCK': '0'})
    def test_real_guard(self):
        with self.assertRaises(RuntimeError):
            gnani.stt(self.audio)

    @patch.dict(os.environ, {'GNANI_MOCK': '0', 'GNANI_API_KEY': 'test-key'})
    @patch('gnani.time.sleep')
    @patch('gnani.requests.post')
    def test_real_cache_retry_and_logging(self, post, sleep):
        busy = Mock(status_code=429)
        busy.json.return_value = {'error': 'busy'}
        good = Mock(status_code=200)
        good.json.return_value = {'transcript': 'दो दिन', 'request_id': 'fixture-id'}
        post.side_effect = [busy, good]
        with patch.object(gnani, '_REAL_SCRIPT', True):
            result = gnani.stt(self.audio, ['Telma 40'], 'question')
            self.assertEqual(gnani.stt(self.audio, ['Telma 40'], 'question'), result)
        self.assertEqual(post.call_count, 2)
        fields = post.call_args.kwargs['data']
        self.assertEqual(json.loads(fields['keyterms']), ['Telma 40'])
        self.assertEqual(fields['previous_text'], 'question')
        self.assertFalse(post.call_args.kwargs['allow_redirects'])
        self.assertEqual(len((self.root / 'logs/api_calls.csv').read_text().splitlines()), 3)


if __name__ == '__main__':
    unittest.main()
