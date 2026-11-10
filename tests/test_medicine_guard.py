import unittest
import meds


def extraction(*names, purpose=None):
    value=[dict(name=n,strength=None,purpose=None) for n in names]
    if purpose:value.append(dict(name=None,strength=None,purpose=purpose))
    return {'medicines':dict(value=value,status='ok',evidence='')}


class MedicineGuardTests(unittest.TestCase):
    def test_denial_and_anatomy_even_if_llm_hallucinates(self):
        text='No medicine, I only have pain in my palm'
        self.assertEqual(meds.parse(text,extracted=extraction('Pan')),[])
        self.assertEqual(meds.guard_extraction(text,extraction('Pan'))['medicines']['value'],[])

    def test_pan_strength(self):
        got=meds.parse('Pan 40 leta hoon',extracted=extraction('Pan'))
        self.assertEqual((got[0]['name'],got[0]['strength']),('Pan','40'))

    def test_denial(self):
        self.assertEqual(meds.guard_extraction('koi dawai nahi',extraction())['medicines']['value'],[])

    def test_purpose_unknown(self):
        got=meds.parse('BP ki goli leta hoon, naam yaad nahi',extracted=extraction(purpose='BP'))
        self.assertEqual(got[0]['display'],'BP medicine (name unknown)')

    def test_scoped_denial_and_positive_short_brand(self):
        got=meds.parse('no BP medicine but I take Dolo',extracted=extraction('Dolo',purpose='BP'))
        self.assertEqual([m['name'] for m in got],['Dolo'])

    def test_requires_llm_gate_and_short_exact_context(self):
        self.assertEqual(meds.parse('Pan 40 leta hoon'),[])
        self.assertEqual(meds.parse('Pan 40 leta hoon',extracted=extraction()),[])
        self.assertEqual(meds.parse('Dolo',extracted=extraction('Dolo')),[])
        self.assertEqual(meds.parse('pain tablet',extracted=extraction('Pan')),[])
        self.assertEqual(meds.parse('palm tablet',extracted=extraction('palm')),[])
        self.assertEqual(meds.parse('ORS leta hoon',extracted=extraction('ORS'))[0]['name'],'ORS')
