import copy
import unittest

import extract_v2 as extraction
import redflags_v2 as flags
from eval import scoring_v2 as scoring


def item(value, status='ok', evidence='own example'):
    return {'value': value, 'status': status, 'evidence': evidence}


def clip(question, value, *, status='ok', transcript='own example', errors=None):
    extracted = {'red_flag_symptoms': item(value, status, transcript if status == 'ok' else '')}
    return {'question': question, 'extracted': extracted, 'validation_errors': errors or [],
            'red_flags': flags.detect(transcript, extracted, question=question, validation_errors=errors)}


class ValidationV2Tests(unittest.TestCase):
    def test_empty_safety_list_and_null_evidence(self):
        for evidence in ['', None, 'not a quote']:
            errors = []
            got = extraction.validate('P4', 'A routine response', {'red_flag_symptoms': item([], evidence=evidence)}, errors=errors)
            self.assertEqual(got['red_flag_symptoms']['status'], 'ok')
            self.assertFalse(errors)
        for evidence in ['', None, 'not a quote']:
            errors = []
            got = extraction.validate('P4', 'A routine response', {'red_flag_symptoms': item(['fainting'], evidence=evidence)}, errors=errors)
            self.assertEqual(got['red_flag_symptoms']['status'], 'unclear')
            self.assertTrue(errors)
        got = extraction.validate('R1', 'yes', {'confirmed': item(True, evidence='yes'), 'correction': item(None, 'unclear', None)})
        self.assertEqual(got['correction'], item(None, 'unclear', ''))

    def test_single_field_wrapper_without_guessing_multi_field(self):
        envelope = item('none')
        self.assertEqual(extraction.validate('P6', 'own example', envelope)['allergies']['value'], 'none')
        followup = item({'question_key':'chills', 'value':False})
        got = extraction.validate('F', 'own example', followup, fields=('follow_up',), question_key='chills')
        self.assertFalse(got['follow_up']['value']['value'])
        got = extraction.validate('P1', 'own example', item(45))
        self.assertTrue(all(v['status'] == 'unclear' for v in got.values()))

    def test_nested_nulls_and_per_field_survival(self):
        raw = {'follow_up': item({'question_key':'frequency_per_day', 'value': {'value': None}}, 'unclear', None),
               'red_flag_symptoms': item([], evidence=None)}
        original = copy.deepcopy(raw)
        errors = []
        got = extraction.validate('F', 'own example', raw, errors=errors)
        self.assertEqual(got['follow_up'], item(None, 'unclear', ''))
        self.assertFalse(errors)
        self.assertEqual(raw, original)
        raw['follow_up'] = item(999)
        got = extraction.validate('F', 'own example', raw)
        self.assertEqual(got['follow_up']['status'], 'unclear')
        self.assertEqual(got['red_flag_symptoms']['status'], 'ok')


class SafetyV2Tests(unittest.TestCase):
    def test_negation_overrides_llm_and_followup(self):
        text = 'I am not breathless after walking; my ankle aches.'
        raw = {'red_flag_symptoms': item(['breathlessness'], evidence=text),
               'follow_up': item({'question_key':'breathless', 'value':True}, evidence=text)}
        checked, info, changes = flags.apply_negation(text, raw)
        self.assertEqual(checked['red_flag_symptoms']['value'], [])
        self.assertFalse(checked['follow_up']['value']['value'])
        self.assertTrue(changes)
        self.assertFalse(flags.detect(text, checked, question='F', keyword_info=info)['alert'])
        self.assertEqual(flags.normalize('चाँद'), 'चांद')
        self.assertIn('fainting', flags.keyword_evidence('कभी बेहोश नहीं हुआ; अभी थोड़ा थका हूँ।')['negated'])

    def test_inability_and_positive_keyword_always_alert(self):
        text = 'No chest pain, but I cannot breathe.'
        raw = {'red_flag_symptoms': item(['breathlessness'], evidence=text)}
        checked, info, _ = flags.apply_negation(text, raw)
        self.assertTrue(flags.detect(text, checked, question='P4', keyword_info=info)['alert'])

    def test_denial_of_another_action_cannot_cancel_a_positive(self):
        text = 'बेहोश हुआ, चोट नहीं लगी।'
        raw = {'red_flag_symptoms': item(['fainting'], evidence='बेहोश हुआ')}
        checked, info, _ = flags.apply_negation(text, raw)
        self.assertIn('fainting', info['present'])
        self.assertNotIn('fainting', info['negated'])
        self.assertEqual(checked['red_flag_symptoms']['value'], ['fainting'])
        self.assertTrue(flags.detect(text, checked, question='P4', keyword_info=info)['alert'])

    def test_standalone_denial_attaches_only_across_comma(self):
        text = 'No, fainting or seizures are not present.'
        raw = {'red_flag_symptoms': item(['fainting'], evidence=text)}
        checked, info, _ = flags.apply_negation(text, raw)
        self.assertIn('fainting', info['negated'])
        self.assertEqual(checked['red_flag_symptoms']['value'], [])
        self.assertFalse(flags.detect(text, checked, question='P4', keyword_info=info)['alert'])
        info = flags.keyword_evidence('No. I fainted yesterday.')
        self.assertIn('fainting', info['present'])
        self.assertNotIn('breathlessness', info['negated'])
        text = 'Earlier I was breathless; now I am not breathless.'
        checked, info, _ = flags.apply_negation(text, raw)
        self.assertTrue(flags.detect(text, checked, question='P4', keyword_info=info)['alert'])

    def test_session_denial_clears_only_uncertainty(self):
        rows = [clip('P2', None, status='unclear'), clip('F', None, status='question'), clip('P4', [])]
        result = flags.resolve_session(rows)
        self.assertFalse(any(c['red_flags']['alert'] for c in result))
        self.assertTrue(result[0]['red_flags']['needs_check_cleared_by_p4'])
        self.assertTrue(rows[0]['red_flags']['alert'])  # v1/input objects untouched
        for value in [['seizure']]:
            result = flags.resolve_session([clip('P2', value), clip('P4', [])])
            self.assertTrue(result[0]['red_flags']['alert'])
        result = flags.resolve_session([clip('P4', None, status='unclear'), clip('P4', [])])
        self.assertTrue(result[0]['red_flags']['alert'])


class ScoringV2Tests(unittest.TestCase):
    def test_independent_concepts_and_frequency(self):
        value = {'summary':'Chest pain and heaviness after climbing', 'symptoms':['chest pain', 'heaviness']}
        self.assertTrue(scoring.setB_complaint(value, ['chest pain', 'chest heaviness']))
        self.assertFalse(scoring.setB_complaint({'summary':'No chest discomfort', 'symptoms':['leg heaviness']}, ['chest heaviness']))
        for frequency in ['daily', 'roz', 'रोज़']:
            value = {'summary':frequency + ' headache', 'symptoms':['headache']}
            self.assertTrue(scoring.setB_complaint(value, ['frequent headaches']))
        value = {'summary':'Intense head pain', 'symptoms':['headache starting Monday']}
        self.assertTrue(scoring.setC_complaint(value, 'severe headache since monday'))
