import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import extract_partB_v2 as engine
import llm
from eval import scoring_partB_v2 as scoring
from eval import run_partB_v2 as runner


def item(value,status='ok',evidence='own phrase'):
    return {'value':value,'status':status,'evidence':evidence}


def raw(value):
    return {'choices':[{'message':{'content':json.dumps(value)}}]}


class PartBTests(unittest.TestCase):
    def test_unchanged_setC_csv_scores_remain_numeric(self):
        source={'speaker':'ch','clip':'C99','question':'P1','condition':'symptom_keyterms_off',
                'status_correct':'1','value_correct':'1','red_flag_correct':'','red_flag':'no',
                'status':'ok','expected_status':'ok','expected_red_flag':'n.a.','validation_error':''}
        rows,summary=runner.build_C([source],{})
        self.assertEqual(rows[0]['value_correct'],1)
        self.assertEqual(summary[0]['value_correct'],1)

    def test_empty_optional_keyterms_csv_cell(self):
        row={'keyterms':'','extracted':'{}','validation_errors':'[]','red_flags':'{}',
             'red_flags_before_session_resolution':'{}','partA_details':'{}','validation_errors_v1':'[]'}
        self.assertIsNone(runner.decode_B(row)['keyterms'])

    def test_reason_separate_and_empty_symptoms_allowed(self):
        text='Scheduled review; my ear aches twice each evening.'
        payload={'complaint':item({'summary':'Ear ache twice each evening','symptoms':['ear ache twice each evening']},evidence='my ear aches twice each evening'),
                 'visit_reason':item('Scheduled review',evidence='Scheduled review'),
                 'red_flag_symptoms':item([],evidence=None)}
        errors=[];got=engine.validate('P2',text,payload,errors=errors)
        self.assertFalse(errors);self.assertEqual(got['visit_reason']['value'],'Scheduled review')
        payload['complaint']=item({'summary':'Scheduled review','symptoms':[]},evidence='Scheduled review')
        payload['visit_reason']=item(None,evidence=None)
        got=engine.validate('P2',text,payload)
        self.assertEqual(got['complaint']['status'],'ok')
        self.assertIsNone(got['visit_reason']['value'])

    def test_zero_days_hours_and_per_field_validation(self):
        text='Six hours ago.'
        payload={'duration_days':item(0,evidence='Six hours'),'duration_hours':item(6,evidence='Six hours')}
        self.assertEqual(engine.validate('P3',text,payload),payload)
        payload['duration_days']=item(-1,evidence='Six hours')
        got=engine.validate('P3',text,payload)
        self.assertEqual(got['duration_days']['status'],'unclear')
        self.assertEqual(got['duration_hours']['value'],6)
        got=engine.validate('P3',text,{'duration_days':item(0,evidence='Six hours')})
        self.assertIsNone(got['duration_hours']['value'])
        self.assertEqual(got['duration_hours']['status'],'ok')

    def test_repair_all_row_types_once_preserving_values(self):
        text='Amoxicillin gives me a rash.'
        original=item(['Amoxicillin'],evidence='allergic to amoxicillin')  # bare single-field envelope
        quotes={'allergies':'Amoxicillin gives me a rash','value':['untrusted replacement']}
        with tempfile.TemporaryDirectory() as d,patch.object(engine,'ROOT',Path(d)),patch('llm.settings',return_value=('fake','openai/gpt-oss-120b')),patch('llm.complete_json',side_effect=[(original,raw(original)),(quotes,raw(quotes))]) as call:
            details={};got=engine.extract('P6',text,allow_real=True,details=details)
            self.assertEqual(call.call_count,2)
            self.assertEqual(got['allergies']['value'],['Amoxicillin'])
            self.assertEqual(got['allergies']['evidence'],'Amoxicillin gives me a rash')
            self.assertFalse(details['validation_errors'])
            self.assertTrue(details['initial_validation_errors'])
            again={};self.assertEqual(engine.extract('P6',text,details=again),got)
            self.assertEqual(call.call_count,2);self.assertTrue(again['result_cache_hit'])

    def test_failed_repair_is_cached_no_semantic_retry(self):
        payload={'token':item(29,evidence='invented')};quote={'token':'still invented'}
        with tempfile.TemporaryDirectory() as d,patch.object(engine,'ROOT',Path(d)),patch('llm.settings',return_value=('fake','model')),patch('llm.complete_json',side_effect=[(payload,raw(payload)),(quote,raw(quote))]) as call:
            for _ in range(2):
                got=engine.extract('P0','My queue number is twenty nine.',allow_real=True)
                self.assertEqual(got['token']['status'],'unclear')
            self.assertEqual(call.call_count,2)

    def test_daily_stop_during_repair_reuses_primary(self):
        payload={'duration_days':item(0,evidence='bad quote')}
        quote={'duration_days':'This afternoon'}
        with tempfile.TemporaryDirectory() as d,patch.object(engine,'ROOT',Path(d)),patch('llm.settings',return_value=('fake','model')):
            with patch('llm.complete_json',side_effect=[(payload,raw(payload)),llm.DailyQuotaError('daily limit')]) as call:
                with self.assertRaises(llm.DailyQuotaError):engine.extract('P3','This afternoon.',allow_real=True)
                self.assertEqual(call.call_count,2)
            with patch('llm.complete_json',return_value=(quote,raw(quote))) as call:
                details={};got=engine.extract('P3','This afternoon.',allow_real=True,details=details)
                self.assertEqual(call.call_count,1)
                self.assertTrue(details['primary_cache_hit'])
                self.assertEqual(got['duration_days']['value'],0)

    def test_schema_error_does_not_trigger_evidence_repair(self):
        payload={'duration_days':item('three',evidence='three')}
        with tempfile.TemporaryDirectory() as d,patch.object(engine,'ROOT',Path(d)),patch('llm.settings',return_value=('fake','model')),patch('llm.complete_json',return_value=(payload,raw(payload))) as call:
            engine.extract('P3','three',allow_real=True)
            self.assertEqual(call.call_count,1)

    def test_purpose_can_supply_only_reason_concepts(self):
        record={'complaint':item({'summary':'daily headache','symptoms':['headache']}),
                'visit_reason':item('BP check-up')}
        self.assertTrue(scoring.complaint_correct(record,['BP check','frequent headaches']))
        record={'complaint':item({'summary':'Scheduling','symptoms':[]}),
                'visit_reason':item('fever check')}
        self.assertFalse(scoring.complaint_correct(record,['fever']))
