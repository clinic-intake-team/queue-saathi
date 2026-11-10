#!/usr/bin/env python3
"""Offline-only keyword v3 rescore of final Part B v2 generations. No API fallback."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import redflags_v3 as flags
from eval import rescore_partA_v2 as A, run_partB_v2 as V2
from eval import run_setB as B, run_setC as C, scoring_partB_v2 as SB, scoring_v2 as SC
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'eval/results'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    names=['setB_per_clip_v3.csv','setB_per_session_v3.csv','setB_summary_v3.csv','setC_per_clip_v3.csv','setC_summary_v3.csv','setB_comparison_v2_v3.csv','setC_comparison_v2_v3.csv','v3_new_alerts.csv','clinical_v3_audit.json']
    if any((OUT/n).exists() for n in names):raise RuntimeError('v3 outputs already exist; refusing overwrite')
    protected=[p for p in OUT.rglob('*') if p.is_file()]+[ROOT/'data/setB_ground_truth.csv',ROOT/'data/setC_ground_truth.csv',ROOT/'eval/scoring_v2.py',ROOT/'eval/scoring_partB_v2.py']
    before={str(p.relative_to(ROOT)):digest(p) for p in protected}
    bsource=A.read_csv(OUT/'setB_per_clip_partB_v2.csv');bsessions=A.read_csv(OUT/'setB_per_session_partB_v2.csv');csource=A.read_csv(OUT/'setC_per_clip_partB_v2.csv')
    clips=[];newalerts=[]
    with patch('requests.sessions.Session.request',side_effect=AssertionError('Offline only')),patch('requests.request',side_effect=AssertionError('Offline only')),patch('requests.post',side_effect=AssertionError('Offline only')),patch('gnani.stt',side_effect=AssertionError('No Prisma')),patch('gnani.tts',side_effect=AssertionError('No Timbre')),patch('llm.complete_json',side_effect=AssertionError('No Groq')):
        for source in bsource:
            clip=V2.decode_B(source)
            checked,info,changes=flags.apply_negation(source['transcript'],clip['extracted'])
            f=flags.detect(source['transcript'],checked,question=source['question'],validation_errors=clip['validation_errors'],keyword_info=info)
            clip.update(extracted=checked,red_flags=f,red_flags_before_session_resolution=copy.deepcopy(f),v3_negation_overrides=changes,invalid_llm_output=bool(clip['validation_errors']))
            clips.append(clip)
        resolved=[];sessions=[]
        for old in bsessions:
            group=flags.resolve_session([c for c in clips if (c['speaker'],c['session'])==(old['speaker'],old['session'])]);resolved.extend(group)
            record=B.assemble(group);byrow={c['row']:c for c in group}
            record['visit_reason']=byrow['P2']['extracted']['visit_reason'];record['duration_hours']=byrow['P3']['extracted'].get('duration_hours',B.envelope())
            truth=json.loads(old['truth_json']);sessions.append(dict(speaker=old['speaker'],session=old['session'],record=record,truth=truth,scores=SB.score_setB(record,truth)))
        oldclips={(r['speaker'],r['session'],r['row']):json.loads(r['red_flags']) for r in bsource}
        for c in resolved:
            old=oldclips[(c['speaker'],c['session'],c['row'])]
            if not old['alert'] and c['red_flags']['alert']:newalerts.append(dict(dataset='B',speaker=c['speaker'],clip=c['session']+'_'+c['row'],condition='',expected_red_flag='',transcript=c['transcript'],keywords=json.dumps(c['red_flags']['keyword_flags'])))
        summaryB=B.summary_rows(sessions,resolved)
        rowsC=[]
        for source in csource:
            checked=json.loads(source['extracted_json']);errors=json.loads(source['validation_error']) if source['validation_error'] else []
            checked,info,changes=flags.apply_negation(source['transcript'],checked)
            f=flags.detect(source['transcript'],checked,question=source['question'],validation_errors=errors,keyword_info=info)
            primary=checked[C.PRIMARY[source['question']]]
            truth={key:source[key] for key in ('expected_status','expected_red_flag','question')};truth.update(clip_id=source['clip'],expected_value=json.loads(source['expected_value']))
            row=dict(source);row.update(extracted_json=json.dumps(checked,ensure_ascii=False),status='needs_check' if source['question']=='P4' and f['status']=='needs_check' else primary['status'],red_flag='yes' if f['alert'] else 'no',red_flag_status=f['status'],keyword_flags=json.dumps(f['keyword_flags'],ensure_ascii=False),llm_flags=json.dumps(f['llm_flags'],ensure_ascii=False),negated_keyword_flags=json.dumps(f['negated_keyword_flags'],ensure_ascii=False),**SC.score_setC(truth,checked,f))
            rowsC.append(row)
            if source['red_flag']!='yes' and f['alert']:newalerts.append(dict(dataset='C',speaker=source['speaker'],clip=source['clip'],condition=source['condition'],expected_red_flag=source['expected_red_flag'],transcript=source['transcript'],keywords=json.dumps(f['keyword_flags'])))
        summaryC=C.summarize(rowsC)
    lookup={(r['speaker'],r['session']):r for r in sessions}
    for c in resolved:c['session_scores_json']=lookup[(c['speaker'],c['session'])]['scores']
    outputSessions=[dict(speaker=s['speaker'],session=s['session'],record_json=json.dumps(s['record'],ensure_ascii=False),truth_json=json.dumps(s['truth'],ensure_ascii=False),scores_json=json.dumps(s['scores'],ensure_ascii=False),complete_record_correct=s['scores']['complete_record_correct']) for s in sessions]
    oldB={(r['speaker'],r['field']):r for r in A.read_csv(OUT/'setB_summary_partB_v2.csv')}
    comparisonB=[dict(speaker=r['speaker'],field=r['field'],v2=oldB[(r['speaker'],r['field'])]['correct']+'/'+oldB[(r['speaker'],r['field'])]['total'],v3=str(r['correct'])+'/'+str(r['total'])) for r in summaryB]
    oldC={(r['condition'],r['speaker']):r for r in A.read_csv(OUT/'setC_summary_partB_v2.csv')}
    metrics=[('status','status_correct','status_total'),('value','value_correct','value_total'),('red_flags_caught','red_flags_caught','red_flags_total'),('false_alarms','false_alarms','false_alarm_total')]
    comparisonC=[dict(condition=r['condition'],speaker=r['speaker'],metric=label,v2=oldC[(r['condition'],r['speaker'])][n]+'/'+oldC[(r['condition'],r['speaker'])][d],v3=str(r[n])+'/'+str(r[d])) for r in summaryC for label,n,d in metrics]
    for name,rows in zip(names[:7],[[A.flatten(c) for c in resolved],outputSessions,summaryB,rowsC,summaryC,comparisonB,comparisonC]):B.write_csv(OUT/name,rows)
    if newalerts:B.write_csv(OUT/names[7],newalerts)
    else:(OUT/names[7]).write_text('dataset,speaker,clip,condition,expected_red_flag,transcript,keywords\n')
    assert len(resolved)==212 and len(sessions)==20 and len(rowsC)==48
    assert all(digest(ROOT/n)==value for n,value in before.items())
    audit={'api_calls':{'Prisma':0,'Groq':0,'Timbre':0},'inputs':'final Part B v2 CSVs; saved transcripts and validated LLM outputs reused','protected_hashes':before,'v2_unchanged':True,'new_alert_rows':len(newalerts),'rules_sha256':{n:digest(ROOT/n) for n in ['redflags_v3.py','redflags_rules_v3.py','extract_v3.py']},'scoring_changes':'none; only red-flag keywords/negation reapplied'}
    (OUT/names[8]).write_text(json.dumps(audit,indent=2)+'\n')
    for r in comparisonB:
        if r['field'] in {'false_alarms','red_flags_caught','complete_record'}:print('B',json.dumps(r))
    for r in comparisonC:
        if r['speaker']=='overall':print('C',json.dumps(r))
    print('New alert rows:',len(newalerts));print('Zero API calls; v2 files unchanged.')
if __name__=='__main__':main()
