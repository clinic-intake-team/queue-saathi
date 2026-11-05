import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import gnani
from eval import run_meds as evaluation


class EvaluationTests(unittest.TestCase):
    def test_spoken_strengths_and_brand_spaces(self):
        cases = [
            ('टेल्मा चालीस', 'Telma', '40'),
            ('Dolo chhe sau pachaas', 'Dolo', '650'),
            ('डोलो छह सौ पचास', 'Dolo', '650'),
            ('Glyco met paanch sau', 'Glycomet', '500'),
            ('Thyronorm pachchees', 'Thyronorm', '25'),
            ('थायरोनॉर्म पच्चीस', 'Thyronorm', '25'),
            ('Ecosprin pachhattar', 'Ecosprin', '75'),
            ('Ecosprin seventy five', 'Ecosprin', '75'),
            ('Dolo six hundred and fifty', 'Dolo', '650'),
            ('Amlong paanch', 'Amlong', '5'),
            ('Rosuvas das', 'Rosuvas', '10'),
            ('Telma forty', 'Telma', '40'),
            ('Thyronorm pachaas', 'Thyronorm', '50'),
            ('टेल्मा ४०', 'Telma', '40'),
        ]
        for transcript, name, strength in cases:
            with self.subTest(transcript=transcript):
                self.assertEqual(evaluation.score(transcript, {'name':name, 'strength':strength}), (True, True))
        self.assertEqual(evaluation.score('Pantocid 40', {'name':'Pan','strength':'40'}), (False, False))
        self.assertEqual(evaluation.score('Telmacol 40', {'name':'Telma','strength':'40'}), (False, False))
        self.assertEqual(evaluation.score('Telma 140', {'name':'Telma','strength':'40'}), (True, False))
        self.assertEqual(evaluation.score('Uprise D three', {'name':'Uprise D3','strength':''}), (True, ''))

    def test_offline_outputs_and_heldout_failures(self):
        paths, truth, terms = evaluation.inputs()
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(evaluation, 'ROOT', Path(folder)), patch.object(gnani, 'stt', return_value={'transcript':'synthetic no matches'}), patch('gnani.requests.post', side_effect=AssertionError('Network forbidden')):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    evaluation.run(paths, truth, terms)
                failures = output.getvalue().split('FAILED clips — ch only:')[1]
                self.assertNotIn('tm', failures)
                self.assertIn('M01', failures)
                self.assertTrue((Path(folder)/'eval/results/setA_summary.csv').is_file())
                import csv
                with (Path(folder)/'eval/results/setA_per_clip.csv').open() as f:
                    rows = list(csv.DictReader(f))
                excluded = [r for r in rows if r['medicine'] in ('name_unknown','none')]
                self.assertTrue(excluded)
                self.assertTrue(all(r['scored']=='0' and r['name_correct']=='' for r in excluded))
                self.assertEqual({r['medicine'] for r in rows if r['clip']=='M20'}, {'Amlong'})

    def test_keyterm_limit(self):
        with self.assertRaises(ValueError):
            gnani.stt_cache_path(__file__, ['x']*201)


if __name__ == '__main__':
    unittest.main()
