"""App routing regression: no extraction/evaluation changes and no provider calls."""
from unittest.mock import patch
import unittest
import test_api_phase3 as support

class RoutineFlowTests(unittest.TestCase):
    setUp=support.PatientFlowTests.setUp
    start=support.PatientFlowTests.start
    answer=support.PatientFlowTests.answer
    def fixture(self,positive=False,unclear=False):
        text='I am here for a routine BP check-up. I do not have any symptoms.' if not positive else 'I am here for a routine BP check-up, but I have a headache today.'
        def field(value,status='ok'):return {'value':value,'status':status,'evidence':text if value is not None else ''}
        complaint=field(None,'unclear') if unclear else field({'summary':'Routine BP check-up','symptoms':['headache'] if positive else []})
        return text,{'complaint':complaint,'visit_reason':field('routine BP check-up'),'red_flag_symptoms':field([])}
    def at_p2(self):return self.answer(self.answer(self.start()))
    def test_routine_without_symptoms_skips_duration_and_can_be_redone(self):
        s=self.at_p2();before=s
        with patch('app.api.main.mock_response',return_value=self.fixture()):s=self.answer(s)
        self.assertEqual(s['question']['id'],'P4');self.assertFalse(s['retry'])
        self.assertEqual(s['question']['total_steps'],8)
        self.assertTrue(s['flow']['routine_visit']);self.assertTrue(s['flow']['skip_followups'])
        self.assertEqual(s['fields']['current_symptoms']['value'],[])
        self.assertNotIn('duration_days',s['fields'])
        response=self.client.post(f"/session/{s['id']}/redo",json={'answer_count':3})
        restored=response.json();self.assertEqual(restored['question']['id'],'P2');self.assertNotIn('flow',restored)
        self.assertNotIn('current_symptoms',restored['fields'])
        self.assertEqual(len(restored['answers']),len(before['answers']))
    def test_explicit_denial_is_a_valid_flow_answer_even_if_complaint_unclear(self):
        s=self.at_p2()
        with patch('app.api.main.mock_response',return_value=self.fixture(unclear=True)):s=self.answer(s)
        self.assertEqual(s['question']['id'],'P4');self.assertFalse(s['retry'])
        self.assertEqual(s['fields']['complaint']['status'],'unclear')
        self.assertEqual(s['fields']['current_symptoms']['status'],'ok')
    def test_routine_visit_with_symptoms_keeps_duration(self):
        s=self.at_p2()
        with patch('app.api.main.mock_response',return_value=self.fixture(positive=True)):s=self.answer(s)
        self.assertEqual(s['question']['id'],'P3');self.assertNotIn('flow',s)
    def test_no_symptoms_never_erases_a_positive_red_flag(self):
        s=self.at_p2();text,fields=self.fixture()
        text+=' But I also have chest pain.'
        with patch('app.api.main.mock_response',return_value=(text,fields)):s=self.answer(s)
        self.assertEqual(s['status'],'red_flag');self.assertNotIn('current_symptoms',s['fields'])
    def test_old_duration_step_accepts_no_symptoms_without_reasking(self):
        from app.api import main
        s=self.at_p2()
        raw=main.load(s['id']);raw['question_id']='P3';raw['index']=3
        raw['fields']['visit_reason']={'value':'routine BP check-up','status':'ok','evidence':'routine BP check-up'}
        main.save(raw);s=self.client.get(f"/session/{s['id']}").json()
        fields={'duration_days':{'value':None,'status':'unclear','evidence':''}}
        with patch('app.api.main.mock_response',return_value=('I have no current symptoms. This is a routine visit.',fields)):s=self.answer(s)
        self.assertEqual(s['question']['id'],'P4');self.assertFalse(s['retry'])
        self.assertTrue(s['flow']['duration_not_applicable'])
        self.assertIsNone(s['fields']['duration_days']['value'])
