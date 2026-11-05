import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import extract
from eval import run_setC as evaluation


def item(value,status='ok',evidence='example'):
    return {'value':value,'status':status,'evidence':evidence}


class SetCEvaluationTests(unittest.TestCase):
    def test_c01_accepts_both_statuses(self):
        target={'clip_id':'C01','question':'P2','expected_status':'unclear','expected_value':{},'expected_red_flag':'n.a.'}
        for status in ('unclear','question'):
            scores=evaluation.score(target,{'complaint':item(None,status)},{'alert':False})
            self.assertEqual(scores['status_correct'],1)
            self.assertEqual(scores['value_correct'],1)

    def test_c07_combines_fields_and_requires_all_information(self):
        value={'summary':'bad headache','symptoms':['headache since Monday']}
        self.assertTrue(evaluation.complaint_correct(value,'severe headache since monday'))
        self.assertFalse(evaluation.complaint_correct({'summary':'headache','symptoms':['headache']},'severe headache since monday'))
        self.assertFalse(evaluation.complaint_correct({'summary':'no throat pain','symptoms':['mild fever']},'throat pain + mild fever'))

    def test_terms_vary_only_for_p2_and_p4(self):
        for question in ('P1','P3'):
            for condition in evaluation.CONDITIONS:
                self.assertIsNone(evaluation.request_terms(question,condition,['med'],['symptom']))
        for question in ('P2','P4'):
            self.assertIsNone(evaluation.request_terms(question,evaluation.CONDITIONS[0],['med'],['symptom']))
            self.assertEqual(evaluation.request_terms(question,evaluation.CONDITIONS[1],['med'],['symptom']),['symptom'])
        for condition in evaluation.CONDITIONS:
            self.assertEqual(evaluation.request_terms('P5',condition,['med'],['symptom']),['med'])

    def test_metrics_separate_silent_wrong_and_safe_miss(self):
        base={'speaker':'ch','question':'P3','expected_status':'ok','expected_red_flag':'n.a.',
              'status_correct':0,'value_correct':0,'red_flag':'no','red_flag_correct':'','validation_error':''}
        rows=[]
        for condition in evaluation.CONDITIONS:
            for status in ('ok','unclear','declined','needs_check','question'):
                rows.append(dict(base,condition=condition,status=status))
        summaries=evaluation.summarize(rows)
        for summary in summaries:
            if summary['speaker']!='tm':
                self.assertEqual(summary['silently_wrong'],1)
                self.assertEqual(summary['safe_miss'],3)

    def test_network_free_synthetic_two_condition_run(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            paths=[root/'ch_C01.m4a',root/'tm_C01.m4a']
            truth={'C01':{'clip_id':'C01','question':'P4','expected_status':'ok',
                         'expected_value':{'red_flag_reason':'breathlessness'},'expected_red_flag':'yes'}}
            def fake_extract(question,text,**kwargs):
                kwargs['details'].update(validation_errors=[{'field':'red_flag_symptoms','error':'missing'}],raw_response={})
                return {'red_flag_symptoms':item(None,'unclear','')}
            with patch.object(evaluation,'ROOT',root), patch.object(evaluation,'verify_build'), patch.object(evaluation,'symptom_terms',return_value=['saans']), patch('gnani.stt',return_value={'transcript':'example'}) as stt, patch('extract.cached_available',return_value=True), patch('extract.extract',side_effect=fake_extract), patch('llm.requests.request',side_effect=AssertionError('network forbidden')), contextlib.redirect_stdout(io.StringIO()):
                rows,summary=evaluation.run(paths,truth,{'P4':'screen'},[],allow_real=True)
            self.assertEqual(len(rows),4)
            self.assertTrue(all(r['status']=='needs_check' and r['red_flag']=='yes' for r in rows))
            self.assertTrue(all(r['value_correct']==0 for r in rows))
            self.assertIsNone(stt.call_args_list[0].kwargs['keyterms'])
            self.assertEqual(stt.call_args_list[2].kwargs['keyterms'],['saans'])
            self.assertEqual(len(summary),6)
            self.assertTrue((root/'eval/results/setC_per_clip.csv').exists())

    def test_plan_is_offline_and_deduplicates_shared_requests(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            paths=[root/'ch_C02.m4a']
            targets={'C02':{'question':'P1'}}
            cache=root/'stt.json';cache.write_text('{"transcript":"example"}')
            with patch.object(evaluation,'symptom_terms',return_value=['saans']), patch('gnani.stt_cache_path',return_value=cache), patch('extract.cache_path',return_value=root/'llm.json'), patch('extract.cached_available',return_value=False), patch('llm.requests.request',side_effect=AssertionError('network forbidden')), contextlib.redirect_stdout(io.StringIO()):
                plan=evaluation.call_plan(paths,targets,{'P1':'age prompt'},[])
            self.assertEqual(plan['prisma_calls'],0)
            self.assertEqual(plan['groq_known_calls'],1)
            self.assertEqual(plan['groq_cache_hits'],1)

    def test_no_run_without_confirmation(self):
        with self.assertRaises(RuntimeError): evaluation.run([],{}, {},[])


if __name__=='__main__': unittest.main()
