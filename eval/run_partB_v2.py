#!/usr/bin/env python3
"""Part B P2/P3 re-extraction with one evidence repair, quota checkpointing and 3-way reporting."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import extract
import extract_partB_v2 as engine
import llm
import redflags_v2
from eval import run_setB as B
from eval import run_setC as C
from eval import rescore_partA_v2 as A
from eval import scoring_partB_v2 as scoring
from eval import scoring_v2

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'eval/results'
FINAL_NAMES = ['setB_per_clip_partB_v2.csv', 'setB_per_session_partB_v2.csv',
               'setB_summary_partB_v2.csv', 'setC_per_clip_partB_v2.csv',
               'setC_summary_partB_v2.csv', 'setB_threeway_partB_v2.csv', 'setC_threeway_partB_v2.csv']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    return (A.read_csv(OUT / 'setB_per_clip_v2.csv'), A.read_csv(OUT / 'setB_per_session_v2.csv'),
            A.read_csv(OUT / 'setC_per_clip_v2.csv'), A.original_setC_settings())


def job_id(dataset, row):
    return ':'.join([dataset, row['speaker'], row.get('session', row.get('clip', '')),
                     row.get('row', row['question']), row.get('condition', '')])


def jobs_for(rows_B, rows_C, reference):
    jobs = []
    for dataset, rows in [('B', rows_B), ('C', rows_C)]:
        for row in rows:
            if row['question'] not in {'P2', 'P3'}:
                continue
            base_prompt = None if dataset == 'B' else reference['SYSTEM_PROMPT']
            fields = extract.FIELDS[row['question']] if dataset == 'B' else reference['FIELDS'][row['question']]
            kwargs = dict(fields=fields, base_prompt=base_prompt, question_key=None)
            path = engine.cache_path(row['question'], row['transcript'], **kwargs)
            jobs.append(dict(dataset=dataset, row=row, id=job_id(dataset, row), kwargs=kwargs,
                             cache=path))
    return jobs


def protected_files():
    names = ['setB_per_clip.csv','setB_per_session.csv','setB_summary.csv',
             'setC_per_clip.csv','setC_summary.csv','setB_per_clip_v2.csv','setB_per_session_v2.csv',
             'setB_summary_v2.csv','setC_per_clip_v2.csv','setC_summary_v2.csv','partA_audit_v2.json']
    paths = [OUT / name for name in names]
    paths += [ROOT / name for name in ['extract.py','redflags.py','gnani.py','meds.py','archive/app.py',
        'extract_v2.py','redflags_v2.py','eval/scoring_v2.py','data/setB_ground_truth.csv',
        'data/setC_ground_truth.csv','data/medicines.txt','data/symptoms.txt','prompts.yaml']]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}


def freeze(jobs):
    if llm.settings()[1] != 'openai/gpt-oss-120b' or llm.reasoning_effort() != 'medium':
        raise RuntimeError('Preserve original model and medium reasoning for this comparison')
    manifest = {'phase':'Part B v2', 'model':llm.settings()[1], 'reasoning_effort':'medium',
        'baseline_hashes':protected_files(),
        'source_hashes':{name:digest(ROOT/name) for name in ['extract_partB_v2.py','app_extract_v2.py','archive/app_v2.py',
            'eval/scoring_partB_v2.py','eval/run_partB_v2.py','llm.py','eval/PART_B_PROTOCOL_v2.md']},
        'jobs':{j['id']:j['cache'].stem for j in jobs}}
    path = ROOT / 'eval/partB_protocol_v2.json'
    if path.exists() and json.loads(path.read_text()) != manifest:
        raise RuntimeError('Part B protocol changed after freeze; preserve results and review first')
    if not path.exists():
        path.write_text(json.dumps(manifest,indent=2)+'\n')
    return path, manifest


def plan(jobs):
    seen = set()
    primary = known_repairs = possible_repairs = cache_rows = 0
    by_dataset = {}
    for j in jobs:
        label=j['dataset'];by_dataset.setdefault(label,{'rows':0,'new_primary_calls':0})
        by_dataset[label]['rows'] += 1
        path = j['cache']
        if path in seen or path.exists():
            cache_rows += 1
            continue
        seen.add(path)
        raw_path = path.with_suffix('.primary.response.json')
        repair_path = path.with_suffix('.repair.response.json')
        if raw_path.exists():
            parsed,_=engine._parse_response(raw_path)
            errors=[]
            engine.validate(j['row']['question'],j['row']['transcript'],parsed,
                fields=j['kwargs']['fields'],errors=errors)
            known_repairs += int(bool(engine.evidence_fields(errors)) and not repair_path.exists())
        else:
            primary += 1;possible_repairs += 1;by_dataset[label]['new_primary_calls'] += 1
    count = dict(prisma_calls=0, logical_reextraction_rows=len(jobs), by_dataset=by_dataset,
        new_primary_groq_calls=primary, known_repairs=known_repairs,
        max_additional_repairs=possible_repairs, max_logical_groq_calls=primary+known_repairs+possible_repairs,
        duplicate_or_completed_cache_rows=cache_rows,
        unchanged_rows_reused={'B':212-by_dataset['B']['rows'],'C':48-by_dataset['C']['rows']},
        retry_policy='up to five retries for minute/5xx; daily 429 saves and exits')
    print('PART B PLAN '+json.dumps(count),flush=True)
    (ROOT/'eval/partB_call_plan_v2.json').write_text(json.dumps(count,indent=2)+'\n')
    return count


def decode_B(row):
    result=dict(row)
    for key in ['extracted','validation_errors','red_flags','red_flags_before_session_resolution','keyterms','partA_details','validation_errors_v1']:
        if isinstance(result.get(key),str):
            result[key]=None if key == 'keyterms' and result[key] == '' else json.loads(result[key])
    result['red_flags']=copy.deepcopy(result['red_flags_before_session_resolution'])
    return result


def build_B(rows,old_sessions,replacements):
    clips=[]
    for row in rows:
        clip=decode_B(row)
        new=replacements.get(job_id('B',row))
        if new:
            clip.update(extracted=new['extracted'],validation_errors=new['validation_errors'],
                invalid_llm_output=bool(new['validation_errors']),red_flags=new['red_flags'],
                raw_llm_response=json.dumps(new['details']['raw_primary'],ensure_ascii=False),
                raw_repair_response=json.dumps(new['details']['raw_repair'],ensure_ascii=False),
                partB_details=new['details'])
        else:
            clip.update(raw_repair_response='null',partB_details={'reused_partA':True})
        clip['red_flags_before_session_resolution']=copy.deepcopy(clip['red_flags'])
        clips.append(clip)
    resolved,sessions=[],[]
    for source in old_sessions:
        group=[c for c in clips if (c['speaker'],c['session'])==(source['speaker'],source['session'])]
        group=redflags_v2.resolve_session(group);resolved.extend(group)
        record=B.assemble(group)
        by_row={c['row']:c for c in group}
        record['visit_reason']=by_row['P2']['extracted']['visit_reason']
        record['duration_hours']=by_row['P3']['extracted'].get('duration_hours',B.envelope())
        truth=json.loads(source['truth_json'])
        sessions.append(dict(speaker=source['speaker'],session=source['session'],record=record,
            truth=truth,scores=scoring.score_setB(record,truth)))
    return resolved,sessions,B.summary_rows(sessions,resolved)


def build_C(rows,replacements):
    output=[]
    for source in rows:
        row=dict(source);new=replacements.get(job_id('C',source))
        for field in ['status_correct','value_correct','red_flag_correct']:
            if row.get(field) not in (None,''):
                row[field]=int(row[field])
        if new:
            checked,errors,flags=new['extracted'],new['validation_errors'],new['red_flags']
            primary=checked[C.PRIMARY[source['question']]]
            status='needs_check' if source['question']=='P4' and flags['status']=='needs_check' else primary['status']
            target=dict(clip_id=source['clip'],question=source['question'],expected_status=source['expected_status'],
                expected_value=json.loads(source['expected_value']),expected_red_flag=source['expected_red_flag'])
            row.update(extracted_json=json.dumps(checked,ensure_ascii=False),status=status,
                validation_error=json.dumps(errors,ensure_ascii=False) if errors else '',
                raw_llm_response=json.dumps(new['details']['raw_primary'],ensure_ascii=False),
                raw_repair_response=json.dumps(new['details']['raw_repair'],ensure_ascii=False),
                red_flag='yes' if flags['alert'] else 'no',red_flag_status=flags['status'],
                keyword_flags=json.dumps(flags['keyword_flags'],ensure_ascii=False),llm_flags=json.dumps(flags['llm_flags'],ensure_ascii=False),
                partB_details=json.dumps(new['details'],ensure_ascii=False),**scoring_v2.score_setC(target,checked,flags))
        else:
            row.update(raw_repair_response='null',partB_details=json.dumps({'reused_partA':True}))
        output.append(row)
    return output,C.summarize(output)


def comparison_B(summary):
    old={(r['speaker'],r['field']):r for r in A.read_csv(OUT/'setB_summary.csv')}
    partA={(r['speaker'],r['field']):r for r in A.read_csv(OUT/'setB_summary_v2.csv')}
    output=[]
    for r in summary:
        key=(r['speaker'],r['field'])
        fmt=lambda x: f"{x['correct']}/{x['total']}" if x else 'n.a.'
        output.append(dict(speaker=r['speaker'],field=r['field'],v1=fmt(old.get(key)),
            v2_partA=fmt(partA.get(key)),v2_partB=fmt(r)))
    return output


def comparison_C(summary):
    previous=A.compare_C(A.read_csv(OUT/'setC_summary.csv'),summary)
    partA={(r['condition'],r['speaker']):r for r in A.read_csv(OUT/'setC_summary_v2.csv')}
    mapping={'status':('status_correct','status_total'),'value':('value_correct','value_total'),
        'red_flags_caught':('red_flags_caught','red_flags_total'),'false_alarms':('false_alarms','false_alarm_total')}
    result=[]
    for row in previous:
        a=partA[(row['condition'],row['speaker'])];metric=row['metric']
        mid=f"{a[mapping[metric][0]]}/{a[mapping[metric][1]]}" if metric in mapping else a[metric]
        result.append(dict(condition=row['condition'],speaker=row['speaker'],metric=metric,
                           v1=row['v1'],v2_partA=mid,v2_partB=row['v2']))
    return result


def run(*,allow_real=False):
    rows_B,sessions_A,rows_C,reference=inputs()
    jobs=jobs_for(rows_B,rows_C,reference)
    protocol_path,protocol=freeze(jobs)
    plan(jobs)
    if not allow_real:
        print('Plan only; no API calls. --real executes the already-authorized Part B run.');return
    if any((OUT/name).exists() for name in FINAL_NAMES):
        raise RuntimeError('Part B final outputs already exist; refuse overwrite')
    checkpoint=ROOT/'cache/partB_checkpoint_v2.json';protocol_hash=digest(protocol_path)
    saved=json.loads(checkpoint.read_text()) if checkpoint.exists() else {'protocol_hash':protocol_hash,'done':{},'http_attempts':0,'elapsed_seconds':0}
    if saved['protocol_hash']!=protocol_hash:raise RuntimeError('Checkpoint protocol differs')
    done=saved['done'];before=llm.STATS['real_calls'];start=time.monotonic();current=None
    def save(status,stop=None):
        state={'protocol_hash':protocol_hash,'done':done,'status':status,
            'http_attempts':saved['http_attempts']+llm.STATS['real_calls']-before,
            'elapsed_seconds':round(saved['elapsed_seconds']+time.monotonic()-start,1),'stop':stop}
        checkpoint.parent.mkdir(exist_ok=True,parents=True)
        tmp=checkpoint.with_suffix('.tmp');tmp.write_text(json.dumps(state,ensure_ascii=False));tmp.replace(checkpoint)
        return state
    try:
        for j in jobs:
            current=j
            if j['id'] in done:continue
            details={}
            checked=engine.extract(j['row']['question'],j['row']['transcript'],allow_real=True,details=details,**j['kwargs'])
            checked,keyword_info,overrides=redflags_v2.apply_negation(j['row']['transcript'],checked)
            errors=details['validation_errors']
            flags=redflags_v2.detect(j['row']['transcript'],checked,question=j['row']['question'],
                validation_errors=errors,keyword_info=keyword_info)
            details['negation_overrides']=overrides
            done[j['id']]={'extracted':checked,'validation_errors':errors,'red_flags':flags,'details':details}
            state=save('running')
            if len(done)%10==0 or len(done)==len(jobs):
                print(json.dumps({'progress':f'{len(done)}/{len(jobs)}','http_attempts':state['http_attempts'],
                    'elapsed_seconds':state['elapsed_seconds'],'prisma_calls':0}),flush=True)
    except llm.DailyQuotaError as exc:
        reset=datetime.fromtimestamp(exc.reset_at,timezone.utc) if exc.reset_at else None
        stop={'job':current['id'] if current else None,'message':exc.server_message or str(exc),
              'wait_hint':exc.wait_hint,'wait_seconds':exc.wait_seconds,
              'reset_utc':reset.isoformat() if reset else None,
              'reset_ist':reset.astimezone(ZoneInfo('Asia/Kolkata')).isoformat() if reset else None,
              'resume_command':'.venv/bin/python eval/run_partB_v2.py --real'}
        state=save('daily_quota_stopped',stop)
        print('DAILY QUOTA STOP '+json.dumps({'completed':len(done),'total':len(jobs),**stop}),flush=True)
        print('Progress and primary/repair response caches saved; 429 is not an invalid field or failed clip.',flush=True)
        return
    clips,sessions,summary_B=build_B(rows_B,sessions_A,done)
    clips_C,summary_C=build_C(rows_C,done)
    lookup={(s['speaker'],s['session']):s for s in sessions}
    output_B=[]
    for c in clips:
        row=A.flatten(c);row['session_scores_json']=json.dumps(lookup[(c['speaker'],c['session'])]['scores'],ensure_ascii=False)
        output_B.append(row)
    output_sessions=[dict(speaker=s['speaker'],session=s['session'],record_json=json.dumps(s['record'],ensure_ascii=False),
        truth_json=json.dumps(s['truth'],ensure_ascii=False),scores_json=json.dumps(s['scores'],ensure_ascii=False),
        complete_record_correct=s['scores']['complete_record_correct']) for s in sessions]
    comparisons_B,comparisons_C=comparison_B(summary_B),comparison_C(summary_C)
    for name,rows in zip(FINAL_NAMES,[output_B,output_sessions,summary_B,clips_C,summary_C,comparisons_B,comparisons_C]):
        B.write_csv(OUT/name,rows)
    if any(digest(ROOT/name)!=expected for name,expected in protocol['baseline_hashes'].items()):
        raise RuntimeError('A protected baseline file changed')
    state=save('complete')
    audit={'phase':'Part B v2','completed_reextraction_rows':len(done),'http_attempts':state['http_attempts'],
        'prisma_calls':0,'baselines_unchanged':True,'protocol_hash':protocol_hash,
        'repair_rows':sum(bool(v['details']['repair_fields']) for v in done.values())}
    (OUT/'partB_audit_v2.json').write_text(json.dumps(audit,indent=2)+'\n')
    for r in comparisons_B:
        if r['field'] in {'complaint','duration_days','red_flags_caught','false_alarms','complete_record','invalid_llm_output','visit_reason'}:
            print('B '+json.dumps(r),flush=True)
    for r in comparisons_C:print('C '+json.dumps(r),flush=True)
    print('Part B complete; v1 and Part A files unchanged.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--real',action='store_true')
    run(allow_real=parser.parse_args().real)
