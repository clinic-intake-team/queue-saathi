#!/usr/bin/env python3
"""Finish the already-complete Part B checkpoint. No API calls; reporting-only fix."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from eval import run_partB_v2 as run
from eval import run_setB as B
from eval import rescore_partA_v2 as A

ROOT=run.ROOT


def main():
    path=ROOT/'eval/partB_protocol_v2.json';protocol=json.loads(path.read_text())
    checkpoint=ROOT/'cache/partB_checkpoint_v2.json';saved=json.loads(checkpoint.read_text())
    if saved['protocol_hash']!=run.digest(path):raise RuntimeError('Checkpoint protocol differs')
    source=Path(run.__file__).read_text()
    before="            result[key]=json.loads(result[key])"
    after="            result[key]=None if key == 'keyterms' and result[key] == '' else json.loads(result[key])"
    for name,expected in protocol['source_hashes'].items():
        if name=='eval/run_partB_v2.py':
            reconstructed=source.replace(after,before)
            reconstructed=reconstructed.replace("        for field in ['status_correct','value_correct','red_flag_correct']:\n            if row.get(field) not in (None,''):\n                row[field]=int(row[field])\n",'')
            actual=hashlib.sha256(reconstructed.encode()).hexdigest()
        else:actual=run.digest(ROOT/name)
        if actual!=expected:raise RuntimeError('Unexpected generation/scoring code change: '+name)
    if any(run.digest(ROOT/name)!=value for name,value in protocol['baseline_hashes'].items()):
        raise RuntimeError('Protected baseline changed')
    if any((run.OUT/name).exists() for name in run.FINAL_NAMES):raise RuntimeError('Final outputs already exist')
    rows_B,sessions_A,rows_C,reference=run.inputs()
    jobs=run.jobs_for(rows_B,rows_C,reference)
    if {j['id']:j['cache'].stem for j in jobs}!=protocol['jobs']:raise RuntimeError('Request identities differ')
    if set(saved['done'])!=set(protocol['jobs']):raise RuntimeError('Not all extractions complete')
    with patch('requests.request',side_effect=AssertionError('No network')),patch('requests.post',side_effect=AssertionError('No network')),patch('llm.complete_json',side_effect=AssertionError('No LLM calls')),patch('gnani.stt',side_effect=AssertionError('No STT calls')):
        clips,sessions,summary_B=run.build_B(rows_B,sessions_A,saved['done'])
        clips_C,summary_C=run.build_C(rows_C,saved['done'])
        comparisons_B=run.comparison_B(summary_B);comparisons_C=run.comparison_C(summary_C)
    assert len(clips)==212 and len(sessions)==20 and len(clips_C)==48
    lookup={(s['speaker'],s['session']):s for s in sessions}
    output_B=[]
    for c in clips:
        row=A.flatten(c);row['session_scores_json']=json.dumps(lookup[(c['speaker'],c['session'])]['scores'],ensure_ascii=False)
        output_B.append(row)
    output_sessions=[dict(speaker=s['speaker'],session=s['session'],record_json=json.dumps(s['record'],ensure_ascii=False),
        truth_json=json.dumps(s['truth'],ensure_ascii=False),scores_json=json.dumps(s['scores'],ensure_ascii=False),
        complete_record_correct=s['scores']['complete_record_correct']) for s in sessions]
    for name,rows in zip(run.FINAL_NAMES,[output_B,output_sessions,summary_B,clips_C,summary_C,comparisons_B,comparisons_C]):
        B.write_csv(run.OUT/name,rows)
    if any(run.digest(ROOT/name)!=value for name,value in protocol['baseline_hashes'].items()):
        raise RuntimeError('Protected baseline changed')
    saved.update(status='complete',finalized_at_utc=datetime.now(timezone.utc).isoformat(),
                 reporting_fix='CSV deserialization only: empty optional keyterms to null and cached numeric score cells to integers; no generation/scoring change')
    checkpoint.write_text(json.dumps(saved,ensure_ascii=False))
    repairs={j['cache'].stem for j in jobs if saved['done'][j['id']]['details']['repair_fields']}
    audit={'phase':'Part B v2','completed_reextraction_rows':len(saved['done']),'http_attempts':saved['http_attempts'],
        'prisma_calls':0,'unique_primary_responses':len({j['cache'].stem for j in jobs}),
        'unique_evidence_repairs':len(repairs),'baselines_unchanged':True,
        'generation_protocol_hash':saved['protocol_hash'],'reporting_only_fix':saved['reporting_fix'],
        'reporting_runner_sha256':run.digest(Path(run.__file__)),
        'offline_finalizer_sha256':run.digest(Path(__file__))}
    (run.OUT/'partB_audit_v2.json').write_text(json.dumps(audit,indent=2)+'\n')
    for r in comparisons_B:
        if r['field'] in {'complaint','duration_days','visit_reason','complete_record','red_flags_caught','false_alarms','invalid_llm_output'}:
            print('B '+json.dumps(r),flush=True)
    for r in comparisons_C:print('C '+json.dumps(r),flush=True)
    print('Finalized all outputs offline; no additional API calls. All baselines unchanged.')


if __name__=='__main__':main()
