import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

import extract
import redflags


class InvalidOutputTests(unittest.TestCase):
    def test_raw_rejection_is_field_unclear_and_never_retried(self):
        raw={'choices':[{'message':{'content':json.dumps({'duration_days':{'value':3,'status':'ok','evidence':'invented'}})}}]}
        response=Mock(text=json.dumps(raw))
        response.json.return_value=raw
        with tempfile.TemporaryDirectory() as folder, patch.object(extract,'ROOT',Path(folder)), patch('llm.settings',return_value=('fake','model')), patch('llm._request',return_value=response) as request:
            for _ in range(2):
                details={}
                got=extract.extract('P3','three days',allow_real=True,details=details)
                self.assertEqual(got['duration_days']['value'],None)
                self.assertEqual(got['duration_days']['status'],'unclear')
                self.assertEqual(details['raw_response'],raw)
                self.assertTrue(details['validation_errors'])
            self.assertEqual(request.call_count,1)

    def test_legacy_rejected_raw_salvages_valid_fields_offline(self):
        parsed={'age':{'value':39,'status':'ok','evidence':'39'},
                'sex':{'value':None,'status':'declined','evidence':'invented'}}
        raw={'choices':[{'message':{'content':json.dumps(parsed)}}]}
        with tempfile.TemporaryDirectory() as folder, patch.object(extract,'ROOT',Path(folder)), patch('llm.settings',return_value=('fake','model')), patch('llm.complete_json',side_effect=AssertionError('no network')):
            cache=extract.cache_path('P1','39 years')
            cache.parent.mkdir(parents=True)
            cache.with_suffix('.invalid.json').write_text(json.dumps({'raw_response':raw,'error':'old policy rejection'}))
            self.assertTrue(extract.cached_available('P1','39 years'))
            got=extract.extract('P1','39 years')
            self.assertEqual(got,parsed)

    def test_p4_blood_and_uncertainty_failsafe(self):
        for text in ['blood tha kal','khoon aana','खून आया था','There was bleeding yesterday.']:
            denial={'red_flag_symptoms':{'value':[],'status':'ok','evidence':text}}
            flags=redflags.detect(text,denial,question='P4')
            self.assertTrue(flags['alert'])
            self.assertIn('blood or bleeding mention',flags['keyword_flags'])
        for text in ['No blood or bleeding.','khoon nahi aaya','खून नहीं आया।']:
            denial={'red_flag_symptoms':{'value':[],'status':'ok','evidence':text}}
            self.assertFalse(redflags.detect(text,denial,question='P4')['alert'])
        for value in [None,{}, {'red_flag_symptoms':{'value':None,'status':'unclear','evidence':''}}, {'red_flag_symptoms':{'value':[],'status':'ok','evidence':''}}]:
            flags=redflags.detect('Unusable answer',value,question='P4')
            self.assertEqual(flags['status'],'needs_check')
            self.assertTrue(flags['alert'])
        self.assertNotIn('blood or bleeding mention',redflags.detect('blood test',question='P2')['keyword_flags'])


if __name__=='__main__': unittest.main()
