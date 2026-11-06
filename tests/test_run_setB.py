import contextlib
import copy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import extract
import llm
from eval import run_setB as evaluation


def item(value, status='ok'):
    return dict(value=value, status=status, evidence='own example')


def synthetic_session():
    # Independently authored fixture, not a Set B recording or transcript.
    truth = dict(speaker='ch', session='S01', token=42, age=38, sex='male',
        complaint_symptoms=['cough'], duration_days=6,
        follow_up_facts={'measured': True, 'temperature_f': 100, 'chills': False},
        medicines=[{'name': 'Crocin', 'strength': None, 'purpose': None}],
        allergies='none', conditions='none', red_flag='no')
    record = {k: item(v) for k, v in {'token': 42, 'age': 38, 'sex': 'male',
        'complaint': {'summary': 'cough', 'symptoms': ['cough']}, 'duration_days': 6,
        'allergies': 'none', 'conditions': 'none', 'red_flag': False}.items()}
    record['followups'] = {k: item(v) for k, v in truth['follow_up_facts'].items()}
    record['medicines'] = item(copy.deepcopy(truth['medicines']))
    record['medicines_raw'] = item(copy.deepcopy(truth['medicines']))
    return record, truth


class SetBTests(unittest.TestCase):
    def test_rows_question_context_and_terms(self):
        self.assertEqual(sum(len(evaluation.expected_rows(f'S{i:02}')) for i in range(1, 11)), 106)
        for sp in ['ch', 'tm']:
            for n in range(1, 11):
                for row in evaluation.expected_rows(f'S{n:02}'):
                    spec = evaluation.request_spec(Path(f'{sp}_S{n:02}_{row}.m4a'), {f'P{i}': 'question' for i in range(8)}, ['med'], ['symptom'])
                    if row.startswith('F') or row in {'P2', 'P4'}:
                        self.assertEqual(spec['keyterms'], ['symptom'])
                    elif row in {'P5', 'R1'}:
                        self.assertEqual(spec['keyterms'], ['med'])
                    else:
                        self.assertIsNone(spec['keyterms'])
        self.assertEqual(evaluation.followup_key('tm', 'S02', 'F1'), 'last_bp')
        self.assertEqual(evaluation.followup_key('ch', 'S03', 'F1'), 'pain_score')
        self.assertEqual(evaluation.followup_key('tm', 'S03', 'F1'), 'pain_location')

    def test_scoring_and_metrics(self):
        record, truth = synthetic_session()
        self.assertEqual(evaluation.score_session(record, truth)['complete_record_correct'], 1)
        record['age'] = item(44)
        record['duration_days'] = item(None, 'unclear')
        scores = evaluation.score_session(record, truth)
        self.assertEqual(scores['fields']['age']['silently_wrong'], 1)
        self.assertEqual(scores['fields']['duration_days']['safe_miss'], 1)
        truth['follow_up_facts']['pain_score'] = None
        scores = evaluation.score_session(record, truth)
        self.assertFalse(scores['complete_truth'])
        self.assertIsNone(scores['complete_record_correct'])
        session = dict(speaker='ch', truth=truth, record=record, scores=scores)
        summary = evaluation.summary_rows([session], [dict(speaker='ch', validation_errors=[{'field': 'age'}])])
        age = next(r for r in summary if r['speaker'] == 'ch' and r['field'] == 'age')
        self.assertEqual(age['silently_wrong'], 1)
        self.assertEqual(age['invalid_llm_output_clips'], 1)

    def test_medicine_counts_bind_strength_to_name(self):
        target = [{'name': 'Telma', 'strength': '40', 'purpose': None}, {'name': 'Amlong', 'strength': '5', 'purpose': None}]
        wrong = [{'name': 'Telma', 'strength': '5', 'purpose': None}, {'name': 'Amlong', 'strength': '40', 'purpose': None}]
        got = evaluation.medicine_counts(wrong, target)
        self.assertEqual(got['names_correct'], 2)
        self.assertEqual(got['strengths_correct'], 0)
        got = evaluation.medicine_counts(wrong + [{'name': 'Crocin'}], target)
        self.assertEqual(got['extra_names'], 1)

    def test_same_day_only_explicit_validation_option(self):
        value = {'duration_days': {'value': 0, 'status': 'ok', 'evidence': 'this morning'}}
        self.assertEqual(extract.validate('P3', 'this morning', value)['duration_days']['status'], 'unclear')
        self.assertEqual(extract.validate('P3', 'this morning', value, allow_same_day=True)['duration_days']['value'], 0)
        record, truth = synthetic_session()
        record['duration_days'] = item(0)
        truth['duration_days'] = [0, 1]
        self.assertTrue(evaluation.score_session(record, truth)['fields']['duration_days']['correct'])

    def test_followup_ranges_temperature_and_negation(self):
        self.assertTrue(evaluation.followup_correct(5.5, {'min': 5, 'max': 6}, 'frequency_per_day'))
        self.assertFalse(evaluation.followup_correct(7, {'min': 5, 'max': 6}, 'frequency_per_day'))
        self.assertEqual(evaluation.measured_temperature('Temperature one hundred tha.'), 100)
        self.assertEqual(evaluation.measured_temperature('38 celsius'), 100.4)
        self.assertEqual(evaluation.measured_temperature('100.4 Fahrenheit'), 100.4)
        self.assertIsNone(evaluation.measured_temperature('Nahi naapa tha.'))
        self.assertFalse(evaluation.concept_matches({'summary': 'no cough', 'symptoms': ['no cough']}, 'cough'))
        self.assertTrue(evaluation.concept_matches({'summary': 'Vomiting occurred', 'symptoms': ['one episode']}, 'vomited once'))
        for location in ['back of head', 'near neck', 'occipital area']:
            self.assertTrue(evaluation.followup_correct(location, ['back of head', 'near neck'], 'pain_location'))
        self.assertFalse(evaluation.followup_correct('left knee', ['back of head', 'near neck'], 'pain_location'))

    def test_plan_offline_exact_stt_upper_bound_groq(self):
        paths = [Path('ch_S01_P0.m4a'), Path('tm_S01_P0.m4a'), Path('ch_S01_P1.m4a')]
        with tempfile.TemporaryDirectory() as directory:
            cached = Path(directory) / 'hit.json'
            cached.write_text('{"transcript":"own example"}')
            missing = Path(directory) / 'missing.json'
            with patch('gnani.stt_cache_path', side_effect=[cached, cached, missing]), patch('extract.cache_path', return_value=Path('same_llm.json')), patch('extract.cached_available', return_value=False), patch('llm._reservation', return_value=2000), patch('llm.rate_limits', return_value={}), patch('llm.estimate_seconds', return_value={}), patch('requests.request', side_effect=AssertionError('Network forbidden')), contextlib.redirect_stdout(io.StringIO()):
                plan = evaluation.call_plan(paths, {'P0': 'token', 'P1': 'age'}, [], [])
            self.assertEqual(plan['prisma_calls'], 1)
            self.assertEqual(plan['prisma_cache_hits'], 2)
            self.assertEqual(plan['groq_known_calls'], 1)
            self.assertEqual(plan['groq_cache_hits'], 1)
            self.assertEqual(plan['groq_max_before_retries'], 2)

    def test_run_gate_and_preserve_existing_results(self):
        with self.assertRaises(RuntimeError): evaluation.run([], {}, {}, [], [])
        with tempfile.TemporaryDirectory() as directory, patch.object(evaluation, 'ROOT', Path(directory)), patch.object(evaluation, 'verify_protocol'):
            p = Path(directory) / 'eval/results/setB_per_clip.csv'
            p.parent.mkdir(parents=True)
            p.write_text('preserve me')
            with self.assertRaises(RuntimeError): evaluation.run([], {}, {}, [], [], allow_real=True)
            self.assertEqual(p.read_text(), 'preserve me')

    def test_full_pipeline_with_synthetic_responses_and_no_network(self):
        record, truth = synthetic_session()
        answers = {'P0': {'token': item(42)}, 'P1': {'age': item(38), 'sex': item('male')},
            'P2': {'complaint': record['complaint'], 'red_flag_symptoms': item([])},
            'P3': {'duration_days': item(6)}, 'P4': {'red_flag_symptoms': item([])},
            'P5': {'medicines': record['medicines']}, 'R1': {'confirmed': item(True), 'correction': item(None, 'unclear')},
            'P6': {'allergies': item('none')}, 'P7': {'conditions': item('none')}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'eval').mkdir()
            (root / 'eval/setB_full_v1_protocol.json').write_text('{}')
            paths = [root / 'recordings' / f'ch_S01_{row}.m4a' for row in evaluation.expected_rows('S01')]
            current = {}
            paid_stt = set()
            stopped_once = []
            def stt(path, **kwargs):
                paid_stt.add(str(path))
                row = evaluation.classify(path)[2]
                current['row'] = row
                return {'transcript': 'Crocin' if row == 'P5' else '100 Fahrenheit' if row == 'F1' else 'own example'}
            def fake_extract(question, text, **kwargs):
                kwargs['details'].update(raw_response={'test': 'simulated'}, validation_errors=[])
                if question == 'F':
                    if current['row'] == 'F1' and not stopped_once:
                        stopped_once.append(True)
                        raise llm.DailyQuotaError('daily quota', reset_at=2000000000, quota='tokens_per_day')
                    value = True if kwargs['question_key'] == 'measured' else False
                    return {'follow_up': dict(item({'question_key': kwargs['question_key'], 'value': value}), evidence=text),
                            'red_flag_symptoms': dict(item([]), evidence=text)}
                return copy.deepcopy(answers[question])
            with patch.object(evaluation, 'ROOT', root), patch.object(evaluation, 'verify_protocol'), patch('gnani.stt', side_effect=stt), patch('extract.extract', side_effect=fake_extract), patch('extract.cached_available', return_value=True), patch('requests.request', side_effect=AssertionError('Network forbidden')), contextlib.redirect_stdout(io.StringIO()):
                result = evaluation.run(paths, {('ch', 'S01'): truth}, {f'P{i}': 'question' for i in range(8)}, ['Crocin'], ['cough'], allow_real=True)
                self.assertIsNone(result)
                saved = json.loads((root / 'cache/setB_full_v1_checkpoint.json').read_text())
                self.assertEqual(saved['status'], 'daily_quota_stopped')
                self.assertEqual(len(saved['clips']), 4)
                self.assertEqual(saved['stop']['pending_clip']['row'], 'F1')
                self.assertTrue(saved['stop']['quota_reset_ist'])
                self.assertFalse((root / 'eval/results/setB_per_clip.csv').exists())
                clips, sessions, summary = evaluation.run(paths, {('ch', 'S01'): truth}, {f'P{i}': 'question' for i in range(8)}, ['Crocin'], ['cough'], allow_real=True)
            self.assertEqual(len(clips), 11)
            self.assertEqual(len(paid_stt), 11)
            self.assertEqual(sessions[0]['scores']['complete_record_correct'], 1)
            for filename in ['per_clip', 'per_session', 'summary']:
                self.assertTrue((root / f'eval/results/setB_{filename}.csv').exists())
