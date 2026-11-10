import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import extract
import redflags
import meds


def item(value, status='ok'):
    return {'value': value, 'status': status, 'evidence': 'answer'}


class Stage2Tests(unittest.TestCase):
    def test_all_followup_types_and_bounds(self):
        valid = {'temperature_f': 99.2, 'chills': False, 'pain_location': 'right knee',
                 'pain_score': 0, 'last_bp': {'systolic': 125, 'diastolic': 82},
                 'last_sugar': 130, 'phlegm': {'present': True, 'colour': None},
                 'breathless': True, 'frequency_per_day': 0, 'measured': False}
        invalid = {'temperature_f': True, 'chills': 'no', 'pain_location': '',
                   'pain_score': 11, 'last_bp': {'systolic': 120}, 'last_sugar': -1,
                   'phlegm': {'present': False, 'colour': 'green'},
                   'breathless': 0, 'frequency_per_day': float('nan'), 'measured': 'yes'}
        for key in valid:
            for value, expected in [(valid[key], 'ok'), (invalid[key], 'unclear')]:
                got = extract.validate('F', 'answer', {
                    'follow_up': item({'question_key': key, 'value': value}),
                    'red_flag_symptoms': item([])}, question_key=key)
                self.assertEqual(got['follow_up']['status'], expected)
                self.assertEqual(got['red_flag_symptoms']['status'], 'ok')
        got = extract.validate('F', 'answer', {'follow_up': item({'question_key': 'chills', 'value': True})}, question_key='measured')
        self.assertEqual(got['follow_up']['status'], 'unclear')

    def test_new_fields_and_per_field_rejection(self):
        for question, field, good, bad in [('P0', 'token', 17, True),
            ('P6', 'allergies', 'unknown', [17]), ('P7', 'conditions', ['BP'], ['hypertension'])]:
            self.assertEqual(extract.validate(question, 'answer', {field: item(good)})[field]['value'], good)
            self.assertEqual(extract.validate(question, 'answer', {field: item(bad)})[field]['status'], 'unclear')
        got = extract.validate('R1', 'answer', {'confirmed': item(False), 'correction': item(123)})
        self.assertEqual(got['confirmed']['value'], False)
        self.assertEqual(got['correction']['status'], 'unclear')
        for status in ['declined', 'question', 'unclear']:
            self.assertEqual(extract.validate('P0', '', {'token': item(None, status)})['token']['status'], status)

    def test_followup_context_separates_caches(self):
        with patch('llm.settings', return_value=('fake', 'model')):
            self.assertNotEqual(extract.cache_path('F', 'yes', question_key='chills'), extract.cache_path('F', 'yes', question_key='measured'))
            with self.assertRaises(extract.ValidationError): extract.cache_path('F', 'yes', question_key='guess')

    def test_safety_layers_fail_safe_and_session_or(self):
        for question in ['P2', 'P4', 'F']:
            self.assertEqual(redflags.detect('answer', {}, question=question)['status'], 'needs_check')
            self.assertTrue(redflags.detect('answer', {'red_flag_symptoms': item(['breathlessness'])}, question=question)['alert'])
            self.assertFalse(redflags.detect('answer', {'red_flag_symptoms': item([])}, question=question)['alert'])
        result = redflags.detect_session([
            {'question': 'P4', 'transcript': 'answer', 'extracted': {'red_flag_symptoms': item([])}},
            {'question': 'F', 'transcript': 'I cannot breathe.', 'extracted': {}}])
        self.assertTrue(result['alert'])

    def test_medicine_strength_attachment_and_unknown_purpose(self):
        got = meds.parse('Telma chaalis aur Amlong paanch',extracted=medicine_items('Telma','Amlong'))
        self.assertEqual([(m['name'], m['strength']) for m in got], [('Telma', '40'), ('Amlong', '5')])
        self.assertEqual(meds.parse('Dolo chhe sau pachaas',extracted=medicine_items('Dolo'))[0]['strength'], '650')
        self.assertEqual(meds.parse('BP ki goli, naam yaad nahi',extracted=medicine_items(purpose='BP'))[0]['display'], 'BP medicine (name unknown)')
        self.assertEqual(meds.parse('Telma aur Amlong five',extracted=medicine_items('Telma','Amlong'))[0]['strength'], None)
        self.assertEqual(meds.parse('Dolo',extracted=medicine_items('Dolo')), [])
        self.assertEqual(meds.parse('Telmaa forty',extracted=medicine_items('Telmaa'))[0]['name'], 'Telma')
        self.assertEqual(meds.parse('Telmaa forty',extracted=medicine_items('Telmaa'), fuzzy=False), [])

    def test_correction_unknown_and_confirmation(self):
        self.assertEqual([m['name'] for m in meds.parse('Telma leta hoon. Telma nahi, Amlong hai.',extracted=medicine_items('Amlong'))], ['Amlong'])
        self.assertEqual(meds.parse('BP के लिए एक गोली है, but नाम याद नहीं आ रहा।',extracted=medicine_items(purpose='BP'))[0]['purpose'], 'BP')
        self.assertEqual(meds.parse('शुगर की गोलियाँ हैं, Glycomet है, दूसरी का नाम याद नहीं।',extracted=medicine_items('Glycomet',purpose='sugar'))[-1]['purpose'], 'sugar')
        medicines = meds.parse('Telma forty',extracted=medicine_items('Telma'))
        self.assertEqual(meds.apply_confirmation(medicines, 'answer', {'confirmed': item(True)})[0]['status'], 'confirmed')
        self.assertEqual(meds.apply_confirmation(medicines, 'answer', {'confirmed': item('yes')})[0]['status'], 'needs_confirmation')


def medicine_items(*names,purpose=None):
    value=[dict(name=n,strength=None,purpose=None) for n in names]
    if purpose:value.append(dict(name=None,strength=None,purpose=purpose))
    return {'medicines':dict(value=value,status='ok',evidence='')}
