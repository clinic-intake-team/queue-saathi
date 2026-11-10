#!/usr/bin/env python3
"""Offline medicine-gate replay. Preserve all earlier outputs; never call providers."""
import copy
import hashlib
import inspect
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import meds
from eval import run_setB as B, run_meds as A, rescore_partA_v2 as IO, run_partB_v2 as V2, scoring_partB_v2 as scoring
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'eval/results'


def main():
    if (OUT/'medicines_audit_v4.json').exists():raise RuntimeError('v4 already exists; refusing overwrite')
    protected={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file()}
    oldclips=IO.read_csv(OUT/'setB_per_clip_v3.csv')
    oldsessions=IO.read_csv(OUT/'setB_per_session_v3.csv')
    resolver=B.resolved_medicines
    clips=[];sessions=[]
    with patch('requests.sessions.Session.request',side_effect=AssertionError('Offline only')),patch('gnani.stt',side_effect=AssertionError('No Prisma')),patch('gnani.tts',side_effect=AssertionError('No Timbre')),patch('llm.complete_json',side_effect=AssertionError('No Groq')),patch.object(B,'resolved_medicines',resolver):
        for raw in oldclips:
            clip=V2.decode_B(raw)
            # Preserve already resolved v3 safety flags, unrelated to medicine rules.
            clip['red_flags']=json.loads(raw['red_flags'])
            clip['medicine_extraction_v3']=None;clip['medicine_candidates_v4']=None
            if clip['question']=='P5':
                clip['medicine_extraction_v3']=copy.deepcopy(clip['extracted'])
                clip['extracted']=meds.guard_extraction(clip['transcript'],clip['extracted'])
                clip['medicine_candidates_v4']=meds.parse(clip['transcript'],extracted=clip['extracted'])
            clips.append(clip)
        for old in oldsessions:
            group=[c for c in clips if (c['speaker'],c['session'])==(old['speaker'],old['session'])]
            record=B.assemble(group);byrow={c['row']:c for c in group}
            record['visit_reason']=byrow['P2']['extracted']['visit_reason']
            record['duration_hours']=byrow['P3']['extracted'].get('duration_hours',B.envelope())
            truth=json.loads(old['truth_json']);scores=scoring.score_setB(record,truth)
            sessions.append(dict(speaker=old['speaker'],session=old['session'],record=record,truth=truth,scores=scores))
        summary=B.summary_rows(sessions,clips)
        oldsummary={(r['speaker'],r['field']):r for r in IO.read_csv(OUT/'setB_summary_v3.csv')}
        comparison=[dict(speaker=r['speaker'],field=r['field'],v3=oldsummary[(r['speaker'],r['field'])]['correct']+'/'+oldsummary[(r['speaker'],r['field'])]['total'],v4=str(r['correct'])+'/'+str(r['total'])) for r in summary]
        lookup={(s['speaker'],s['session']):s for s in sessions}
        for c in clips:c['session_scores_json']=lookup[(c['speaker'],c['session'])]['scores']
        B.write_csv(OUT/'setB_per_clip_v4.csv',[IO.flatten(c) for c in clips])
        B.write_csv(OUT/'setB_per_session_v4.csv',[dict(speaker=s['speaker'],session=s['session'],record_json=json.dumps(s['record'],ensure_ascii=False),truth_json=json.dumps(s['truth'],ensure_ascii=False),scores_json=json.dumps(s['scores'],ensure_ascii=False),complete_record_correct=s['scores']['complete_record_correct']) for s in sessions])
        B.write_csv(OUT/'setB_summary_v4.csv',summary)
        B.write_csv(OUT/'setB_comparison_v3_v4.csv',comparison)
        # Set A is a RAW STT metric, not an LLM/medicine parsing metric. Re-score
        # only ch saved transcripts with the unchanged frozen scorer.
        rows=IO.read_csv(OUT/'setA_per_clip.csv');rows=[r for r in rows if r['speaker']=='ch']
        for r in rows:
            if r['scored']=='1':
                name,strength=A.score(r['transcript'],dict(name=r['medicine'],strength=r['strength']))
                r.update(name_correct=int(name),strength_correct=int(strength) if strength!='' else '')
        B.write_csv(OUT/'setA_per_clip_v4.csv',rows)
        a_summary=[]
        for condition in ['keyterms_off','keyterms_on']:
            selected=[r for r in rows if r['condition']==condition and r['scored']=='1']
            strengths=[r for r in selected if r['strength_correct']!='']
            n=sum(int(r['name_correct']) for r in selected);sn=sum(int(r['strength_correct']) for r in strengths)
            a_summary.append(dict(speaker='ch',condition=condition,names_correct=n,names_total=len(selected),name_accuracy=n/len(selected),name_strength_correct=sn,name_strength_total=len(strengths),name_strength_accuracy=sn/len(strengths)))
        B.write_csv(OUT/'setA_summary_v4.csv',a_summary)
        baseline={r['condition']:r for r in IO.read_csv(OUT/'setA_summary.csv') if r['speaker']=='ch'}
        acomp=[dict(speaker='ch',condition=r['condition'],metric=label,v3=baseline[r['condition']][n]+'/'+baseline[r['condition']][d],v4=str(r[n])+'/'+str(r[d]),baseline_note='Original frozen raw-STT result; no separate Set A v3 or cached LLM extraction exists') for r in a_summary for label,n,d in [('names','names_correct','names_total'),('name_strength','name_strength_correct','name_strength_total')]]
        B.write_csv(OUT/'setA_comparison_v3_v4.csv',acomp)
    assert len(clips)==212 and len(sessions)==20
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
    audit=dict(api_calls={'Prisma':0,'Groq':0,'Timbre':0},protected_hashes=protected,previous_outputs_unchanged=True,setA_scope='ch only; original raw STT benchmark re-scored; no cached LLM output exists to evaluate candidate gating',scoring_changes='none',setB_clips=len(clips),setB_sessions=len(sessions))
    (OUT/'medicines_audit_v4.json').write_text(json.dumps(audit,indent=2)+'\n')
    for row in acomp:print('A',json.dumps(row))
    for row in comparison:
        if row['field'].startswith('medicines') or row['field'] in {'complete_record','red_flags_caught','false_alarms'}:print('B',json.dumps(row))

if __name__=='__main__':main()
