import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import extract
import redflags


def item(value,evidence='test',status='ok'):
    return {'value':value,'status':status,'evidence':evidence}


class ExtractionTests(unittest.TestCase):
    def test_bad_age_does_not_remove_valid_sex(self):
        for age in (True,-1,111,'52',52.5,None):
            errors=[]
            result=extract.validate('P1','test',{'age':item(age),'sex':item('female')},errors=errors)
            self.assertEqual(result['age'],item(None,'','unclear'))
            self.assertEqual(result['sex'],item('female'))
            self.assertEqual(errors[0]['field'],'age')

    def test_null_fields_need_no_quote_but_nonnull_fields_do(self):
        for status in ('declined','question','unclear'):
            expected={'age':item(None,'not in transcript',status),'sex':item('female')}
            self.assertEqual(extract.validate('P1','test',expected),expected)
        result=extract.validate('P1','test',{'age':item(44),'sex':item('male','invented')})
        self.assertEqual(result['age']['value'],44)
        self.assertEqual(result['sex']['status'],'unclear')
        result=extract.validate('P4','test',{'red_flag_symptoms':item([],'')})
        self.assertEqual(result['red_flag_symptoms']['status'],'unclear')

    def test_invalid_duration_and_malformed_root_become_unclear(self):
        for value in (True,0,-2,float('inf'),float('nan'),'7'):
            got=extract.validate('P3','test',{'duration_days':item(value)})
            self.assertEqual(got['duration_days'],item(None,'','unclear'))
        got=extract.validate('P1','test',None)
        self.assertTrue(all(v['status']=='unclear' for v in got.values()))
        with self.assertRaises(extract.ValidationError): extract.validate('invalid','test',{})

    def test_valid_field_shapes(self):
        cases=[('P1',{'age':item(0),'sex':item('other')}),
               ('P2',{'complaint':item({'summary':'Ear pain','symptoms':['ear pain']})}),
               ('P3',{'duration_days':item(0.5)}),
               ('P4',{'red_flag_symptoms':item([])}),
               ('P5',{'medicines':item([{'name':None,'strength':None,'purpose':'BP'}])})]
        for question,value in cases: self.assertEqual(extract.validate(question,'test',value),value)

    def test_number_words(self):
        for text,value in [('baavan',52),('बावन',52),('fifty-two',52),('parson se',2),('pichhle hafte se',7)]:
            self.assertEqual(extract.number_words(text),value)

    def test_provider_cache_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(extract,'ROOT',Path(directory)), patch('llm.settings',return_value=('fake','model')):
            result={'age':item(44),'sex':item('male','invented')}
            with patch('llm.complete_json',return_value=(result,{})) as call:
                for _ in range(2):
                    details={}
                    got=extract.extract('P1','test',allow_real=True,details=details)
                    self.assertEqual(got['age']['value'],44)
                    self.assertEqual(got['sex']['status'],'unclear')
                    self.assertEqual(details['validation_errors'][0]['field'],'sex')
                self.assertEqual(call.call_count,1)

    def test_negation_and_either_layer(self):
        for text in ['No chest pain or breathlessness.','Seene mein dard nahi hua.','Saans lene mein koi dikkat nahi hai.','I never fainted.','I feel mildly dizzy.']:
            self.assertFalse(redflags.detect(text)['alert'])
        for text in ['I cannot breathe.','Saans nahi aa rahi.','I vomited blood yesterday.','Stiff neck and high fever.']:
            self.assertTrue(redflags.detect(text)['alert'])


if __name__=='__main__': unittest.main()
