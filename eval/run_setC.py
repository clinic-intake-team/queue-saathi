#!/usr/bin/env python3
"""Set C evaluator. Default is a network-free call plan; --real requires confirmation."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml
import extract
import gnani
import llm
import redflags

ROOT = gnani.ROOT
PRIMARY = {'P1':'age', 'P2':'complaint', 'P3':'duration_days',
           'P4':'red_flag_symptoms', 'P5':'medicines'}
# Frozen, deterministic English paraphrase matching; no grading LLM calls.
COMPLAINT_CONCEPTS = {
    'severe headache since monday': [
        r'\b(?:headache|head pain|pain in (?:my |the )?head)\b',
        r'\b(?:severe|intense|bad|strong)\b', r'\bmonday\b'],
    'throat pain': [r'\b(?:sore throat|throat (?:pain|soreness)|pain in (?:my |the )?throat)\b'],
    'mild fever': [r'\b(?:fever|febrile|temperature)\b', r'\b(?:mild|slight|low[ -]grade)\b'],
    'cough worse at night': [r'\bcough\w*\b', r'\b(?:night|nighttime|nocturnal)\b'],
    'evening fever': [r'\b(?:fever|febrile|temperature)\b', r'\bevenings?\b'],
    'weakness': [r'\b(?:weak\w*|fatigue|tired\w*|lack of (?:energy|strength))\b'],
}
FLAG_CONCEPTS = {
    'breathlessness': r'breathless\w*|shortness of breath|difficulty breathing|breathing difficulty|trouble breathing',
    'vomiting blood': r'vomit\w*.*blood|blood.*vomit\w*|hematemesis|haematemesis',
}


def _norm(text):
    return re.sub(r'\s+', ' ', text.lower()).strip()


def _affirmative_match(text, pattern):
    """Reject directly negated summary clauses without another LLM call."""
    for clause in re.split(r'[.;!?]|\b(?:but|however)\b', _norm(text)):
        if re.search(pattern, clause) and not re.search(r'\b(?:no|not|denies|denied|without|absent)\b', clause):
            return True
    return False


def complaint_correct(value, expected):
    if not isinstance(value, dict):
        return False
    # Use the summary and symptom entries independently so one symptom's modifiers
    # cannot be borrowed from a different symptom in the list.
    passages = [value['summary'], *value['symptoms']]
    for concept in expected.lower().split(' + '):
        patterns = COMPLAINT_CONCEPTS.get(concept)
        if patterns is None:
            raise ValueError(f'No frozen complaint rubric for {concept}')
        if not all(any(_affirmative_match(passage, p) for passage in passages) for p in patterns):
            return False
    return True


def score(truth, extracted, flags):
    field = PRIMARY[truth['question']]
    item = extracted[field]
    accepted = {'unclear', 'question'} if truth.get('clip_id') == 'C01' else {truth['expected_status']}
    actual_status = 'needs_check' if truth['question']=='P4' and flags.get('status')=='needs_check' else item['status']
    status_ok = actual_status in accepted
    expected = truth['expected_value']
    value = item['value']
    if truth['expected_status'] != 'ok':
        # Prevent guessed age/medicines being counted as correct non-answers.
        value_ok = status_ok and value is None
    elif item['status'] != 'ok':
        value_ok = False
    elif field == 'age':
        value_ok = value == expected['age']
    elif field == 'duration_days':
        value_ok = value == expected['duration_days']
    elif field == 'complaint':
        value_ok = complaint_correct(value, expected['complaint'])
    elif field == 'red_flag_symptoms':
        if truth['expected_red_flag'] == 'no':
            value_ok = value == []
        else:
            pattern = FLAG_CONCEPTS[expected['red_flag_reason']]
            value_ok = any(_affirmative_match(v, pattern) for v in value)
    else:
        raise ValueError('Unsupported value scoring case')
    flag_ok = ''
    if truth['question'] == 'P4':
        flag_ok = int(flags['alert'] == (truth['expected_red_flag'] == 'yes'))
    return {'status_correct':int(status_ok), 'value_correct':int(value_ok),
            'red_flag_correct':flag_ok}


def verify_build():
    snapshot = ROOT/'eval/setC_development_v2_protocol.json'
    if not snapshot.exists():
        return
    for file, expected in json.loads(snapshot.read_text())['files'].items():
        if hashlib.sha256((ROOT/file).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Development v2 protocol changed: {file}')


def inputs():
    verify_build()
    with (ROOT/'data/setC_ground_truth.csv').open(encoding='utf-8',newline='') as stream:
        source=list(csv.DictReader(stream))
    truth={}
    for row in source:
        clip=row['clip_id']
        if clip in truth:
            raise ValueError(f'Duplicate ground truth ID: {clip}')
        row['expected_value']=json.loads(row['expected_value'])
        if row['question'] not in PRIMARY or row['expected_status'] not in extract.STATUSES:
            raise ValueError(f'Invalid ground truth: {clip}')
        if row['question']=='P4' and row['expected_red_flag'] not in ('yes','no'):
            raise ValueError(f'Missing P4 red-flag label: {clip}')
        truth[clip]=row
    if set(truth) != {f'C{i:02}' for i in range(1,13)}:
        raise ValueError('Expected C01–C12 ground truth')
    prompts=yaml.safe_load((ROOT/'prompts.yaml').read_text(encoding='utf-8'))
    for question in PRIMARY:
        if not isinstance(prompts.get(question),str) or not prompts[question].strip():
            raise ValueError(f'Missing question text: {question}')
    terms=[line.strip() for line in (ROOT/'data/medicines.txt').read_text().splitlines() if line.strip()]
    if not 1<=len(terms)<=200:
        raise ValueError('Invalid medicine keyterms')
    paths=sorted((ROOT/'recordings').glob('*_C??.m4a'))
    ids=[]
    for path in paths:
        match=re.fullmatch(r'(ch|tm)_(C\d{2})\.m4a',path.name)
        if not match:
            raise ValueError(f'Unexpected filename: {path.name}')
        if not path.stat().st_size:
            raise ValueError(f'Empty recording: {path.name}')
        seconds=gnani._file_seconds(path,path.read_bytes())
        if seconds == '' or not 0<seconds<30:
            raise ValueError(f'Duration unavailable or out of range: {path.name}')
        ids.append((match[1],match[2]))
    if len(ids)!=24 or set(ids)!={(s,f'C{i:02}') for s in ('ch','tm') for i in range(1,13)}:
        raise ValueError('Expected exactly 12 M4A recordings per speaker, C01–C12')
    return paths,truth,prompts,terms


def _cached_transcript(path):
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or not isinstance(data.get('transcript'),str):
        raise ValueError('Invalid cached STT response')
    return data['transcript']


CONDITIONS = ('symptom_keyterms_off', 'symptom_keyterms_on')


def symptom_terms():
    terms = [line.strip() for line in (ROOT/'data/symptoms.txt').read_text().splitlines() if line.strip()]
    if not 1 <= len(terms) <= 200 or len(set(terms)) != len(terms):
        raise ValueError('Symptom terms must be 1–200 unique terms')
    return terms


def request_terms(question, condition, medicines, symptoms):
    if question == 'P5':
        return medicines
    if question in ('P2', 'P4') and condition == 'symptom_keyterms_on':
        return symptoms
    return None


def tasks(paths, truth, medicines, symptoms):
    for condition in CONDITIONS:
        for path in paths:
            speaker, clip = path.stem.split('_')
            question = truth[clip]['question']
            yield condition, path, speaker, clip, question, request_terms(question,condition,medicines,symptoms)


def call_plan(paths,truth,prompts,terms):
    symptoms = symptom_terms()
    counts = {condition: dict(prisma_calls=0,prisma_cache_hits=0,groq_known_calls=0,
                              groq_cache_hits=0,groq_pending_transcripts=0) for condition in CONDITIONS}
    seen_stt, seen_llm = set(), set()
    for condition,path,speaker,clip,question,keyterms in tasks(paths,truth,terms,symptoms):
        count = counts[condition]
        cache = gnani.stt_cache_path(path,keyterms,context=prompts[question],mock=False)
        if cache.exists():
            count['prisma_cache_hits'] += 1
            transcript = _cached_transcript(cache)
            key = extract.cache_path(question,transcript)
            if extract.cached_available(question,transcript) or key in seen_llm:
                count['groq_cache_hits'] += 1
            else:
                count['groq_known_calls'] += 1
            seen_llm.add(key)
        else:
            if cache in seen_stt:
                count['prisma_cache_hits'] += 1
            else:
                count['prisma_calls'] += 1
            count['groq_pending_transcripts'] += 1
        seen_stt.add(cache)
    for condition, count in counts.items():
        print(f"{condition}: Prisma {count['prisma_calls']} calls / {count['prisma_cache_hits']} cache hits; "
              f"Groq {count['groq_known_calls']} known calls / {count['groq_cache_hits']} cache hits / "
              f"{count['groq_pending_transcripts']} depend on new transcripts.")
    total = {key:sum(count[key] for count in counts.values()) for key in next(iter(counts.values()))}
    print(f"TOTAL: {total['prisma_calls']} Prisma + up to {total['groq_known_calls']+total['groq_pending_transcripts']} Groq calls before retries.")
    print('Two 24-clip conditions; non-P2/P4 requests are identical and reuse the same caches.')
    print('One historical rejected response has no retained payload; if still uncached under v2 it needs one fresh extraction, not repeated attempts until valid.')
    print('429/5xx may cause up to 3 HTTP attempts per uncached request; invalid content is never retried.')
    return total


def _log_rows(path):
    if not path.exists(): return []
    with path.open(encoding='utf-8',newline='') as stream:
        return list(csv.DictReader(stream))


def _write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.csv.tmp')
    with temporary.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def summarize(rows):
    result=[]
    for condition in CONDITIONS:
        for speaker in ('overall','ch','tm'):
            group=[r for r in rows if r['condition']==condition and (speaker=='overall' or r['speaker']==speaker)]
            positives=[r for r in group if r['question']=='P4' and r['expected_red_flag']=='yes']
            negatives=[r for r in group if r['question']=='P4' and r['expected_red_flag']=='no']
            status=sum(r['status_correct'] for r in group)
            values=sum(r['value_correct'] for r in group)
            n=len(group)
            result.append(dict(condition=condition,speaker=speaker,status_correct=status,status_total=n,
                status_accuracy=status/n if n else '',value_correct=values,value_total=n,
                value_accuracy=values/n if n else '',red_flags_caught=sum(r['red_flag']=='yes' for r in positives),
                red_flags_total=len(positives),false_alarms=sum(r['red_flag']=='yes' for r in negatives),
                false_alarm_total=len(negatives),
                silently_wrong=sum(r['status']=='ok' and not r['value_correct'] for r in group),
                safe_miss=sum(r['expected_status']=='ok' and r['status'] in ('unclear','declined','needs_check') for r in group),
                needs_check=sum(r['status']=='needs_check' for r in group),
                clips_with_invalid_fields=sum(bool(r['validation_error']) for r in group)))
    return result


def run(paths,truth,prompts,terms,*,allow_real=False):
    if not allow_real:
        raise RuntimeError('Set C real run requires explicit confirmation')
    verify_build()
    symptoms=symptom_terms()
    before_llm=len(_log_rows(ROOT/'logs/llm_calls.csv'))
    gnani.STATS.update(real_calls=0,cache_hits=0)
    llm_hits=0
    old_mock=os.environ.get('GNANI_MOCK')
    old_real=gnani._REAL_SCRIPT
    os.environ['GNANI_MOCK']='0'
    gnani._REAL_SCRIPT=True
    rows=[]
    try:
        for condition,path,speaker,clip,question,keyterms in tasks(paths,truth,terms,symptoms):
            target=truth[clip]
            response=gnani.stt(path,keyterms=keyterms,context=prompts[question])
            transcript=response.get('transcript')
            if not isinstance(transcript,str):
                raise ValueError('STT response has no valid transcript')
            llm_hits+=int(extract.cached_available(question,transcript))
            details={}
            result=extract.extract(question,transcript,allow_real=True,details=details)
            issues=details.get('validation_errors',[])
            flags=redflags.detect(transcript,result,question=question,validation_errors=issues)
            primary=result[PRIMARY[question]]
            status='needs_check' if question=='P4' and flags['status']=='needs_check' else primary['status']
            raw=details.get('raw_response')
            scores=score(target,result,flags)
            row=dict(speaker=speaker,clip=clip,question=question,condition=condition,
                symptom_keyterms_applied=int(question in ('P2','P4') and condition=='symptom_keyterms_on'),
                transcript=transcript,status=status,validation_error=json.dumps(issues,ensure_ascii=False) if issues else '',
                raw_llm_response=json.dumps(raw,ensure_ascii=False),raw_response_available=int(raw is not None),
                extracted_json=json.dumps(result,ensure_ascii=False),red_flag='yes' if flags['alert'] else 'no',
                red_flag_status=flags['status'],keyword_flags=json.dumps(flags['keyword_flags'],ensure_ascii=False),
                llm_flags=json.dumps(flags['llm_flags'],ensure_ascii=False),expected_status=target['expected_status'],
                expected_value=json.dumps(target['expected_value'],ensure_ascii=False),
                expected_red_flag=target['expected_red_flag'],**scores)
            rows.append(row)
            print(f'Completed {len(rows)}/{len(paths)*2}: {speaker}_{clip} {condition}',flush=True)
    finally:
        if old_mock is None: os.environ.pop('GNANI_MOCK',None)
        else: os.environ['GNANI_MOCK']=old_mock
        gnani._REAL_SCRIPT=old_real
        after_llm=len(_log_rows(ROOT/'logs/llm_calls.csv'))
        print(f"Actual HTTP attempts — Prisma: {gnani.STATS['real_calls']}, Groq: {after_llm-before_llm}; cache hits — Prisma: {gnani.STATS['cache_hits']}, Groq: {llm_hits}")
    summary=summarize(rows)
    # Keep the previous run intact as the v1 development baseline.
    import shutil
    for name in ('setC_per_clip','setC_summary'):
        old=ROOT/f'eval/results/{name}.csv'
        backup=ROOT/f'eval/results/{name}_v1.csv'
        if old.exists() and not backup.exists():
            shutil.copy2(old,backup)
    _write_csv(ROOT/'eval/results/setC_per_clip.csv',rows)
    _write_csv(ROOT/'eval/results/setC_summary.csv',summary)
    print('Condition | Speaker | Status | Value | Flags caught | False alarms | Silently wrong | Safe miss | Needs check')
    for s in summary:
        print(f"{s['condition']} | {s['speaker']} | {s['status_correct']}/{s['status_total']} | {s['value_correct']}/{s['value_total']} | "
              f"{s['red_flags_caught']}/{s['red_flags_total']} | {s['false_alarms']}/{s['false_alarm_total']} | "
              f"{s['silently_wrong']} | {s['safe_miss']} | {s['needs_check']}")
    print('Development-set failures (both speakers):')
    for row in rows:
        if not row['status_correct'] or not row['value_correct'] or row['red_flag_correct']==0:
            print(json.dumps({key:row[key] for key in ('speaker','clip','condition','transcript','status',
                'validation_error','expected_status','expected_value','expected_red_flag','extracted_json','red_flag')},ensure_ascii=False))
    return rows,summary


def freeze_inputs(paths):
    files=['eval/run_setC.py','extract.py','redflags.py','llm.py','gnani.py',
           'data/setC_ground_truth.csv','data/medicines.txt','data/symptoms.txt','prompts.yaml',
           'eval/SCORING_NOTES.md']
    hashes={file:hashlib.sha256((ROOT/file).read_bytes()).hexdigest() for file in files}
    audio={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    path=ROOT/'eval/setC_development_v2_protocol.json'
    payload={'model':llm.settings()[1],'files':hashes,'audio':audio}
    if path.exists():
        if json.loads(path.read_text())!=payload:
            raise ValueError('Set C protocol or recordings changed after the call-count gate; review required')
    else:
        path.write_text(json.dumps(payload,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real',action='store_true',help='Request a run, with a second interactive call gate')
    args=parser.parse_args()
    paths,truth,prompts,terms=inputs()
    freeze_inputs(paths)
    print('Set C development v2 protocol fingerprinted; previous results preserved until approved run completes.')
    print('LLM model: '+llm.settings()[1])
    call_plan(paths,truth,prompts,terms)
    if not args.real:
        print('STOP: dry plan only. No API calls or evaluation results produced.')
        return
    if input('Type RUN SET C to authorize these evaluation calls: ')!='RUN SET C':
        raise SystemExit('Cancelled without API calls.')
    run(paths,truth,prompts,terms,allow_real=True)


if __name__=='__main__': main()
