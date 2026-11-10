import unittest
import extract_v3
import redflags_v3

class ClinicalV3Tests(unittest.TestCase):
    def test_new_conditions_and_evidence(self):
        text='Mujhe TB, dil ki bimari aur mirgi hai.'
        for value in [['TB'],['heart disease'],['epilepsy'],['TB','heart disease','epilepsy']]:
            errors=[];got=extract_v3.validate('P7',text,{'conditions':{'value':value,'status':'ok','evidence':text}},errors=errors)
            self.assertEqual(errors,[]);self.assertEqual(got['conditions']['value'],value)
        errors=[];got=extract_v3.validate('P7',text,{'conditions':{'value':['TB'],'status':'ok','evidence':'invented'}},errors=errors)
        self.assertTrue(errors);self.assertIsNone(got['conditions']['value'])
    def test_new_flags_and_denials(self):
        examples=[('New confusion started today.','No new confusion.'),('Mujhe behosh jaisa lagta hai.','Mujhe behosh jaisa nahi lagta.'),('Mujhe samajh nahi aa raha.','Mujhe confusion nahi hai.'),('Severe abdominal pain.','No severe abdominal pain.'),('Pet mein bahut tez dard hai.','Pet mein bahut tez dard nahi hai.'),('My tongue is swollen.','My tongue is not swollen.'),('Chehra soojh gaya hai.','Chehra soojh nahi gaya.'),('Sudden vision loss.','No sudden vision loss.'),('Achanak dikhna band ho gaya.','Achanak dikhna band nahi hua.')]
        for positive,negative in examples:
            with self.subTest(positive=positive):
                self.assertTrue(redflags_v3.keyword_evidence(positive)['present'])
                self.assertFalse(redflags_v3.keyword_evidence(negative)['present'])
