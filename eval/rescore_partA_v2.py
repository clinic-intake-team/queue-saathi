#!/usr/bin/env python3
"""Part A: offline revalidation/re-scoring of saved generations. No provider calls."""
import ast
import copy
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import extract_v2
import redflags_v2
from eval import run_setB as B
from eval import run_setC as C
from eval import scoring_v2

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def original_setC_settings():
    ref = json.loads((ROOT / 'eval/setC_reasoning_reference.json').read_text())['git_commit']
    source = subprocess.check_output(['git', 'show', ref + ':extract.py'], cwd=ROOT)
    snapshot = json.loads((ROOT / 'eval/setC_development_v2_protocol.json').read_text())
    if hashlib.sha256(source).hexdigest() != snapshot['files']['extract.py']:
        raise RuntimeError('Set C baseline source fingerprint differs')
    values = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {'FIELDS', 'SYSTEM_PROMPT'}:
                    values[target.id] = ast.literal_eval(node.value)
    values['model'] = snapshot['model']
    return values


def generation(row, reference=None):
    raw = json.loads(row.get('raw_llm_response', 'null'))
    if raw is not None:
        try:
            return json.loads(raw['choices'][0]['message']['content']), 'raw_response_in_v1_csv'
        except (KeyError, TypeError, IndexError, ValueError):
            return None, 'malformed_raw_response_in_v1_csv'
    if reference is None:
        raise RuntimeError('Original LLM generation unavailable; refusing to call API or invent it')
    payload = {'provider': 'groq', 'model': reference['model'], 'question': row['question'],
               'transcript': row['transcript'], 'prompt': reference['SYSTEM_PROMPT']}
    key = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    path = ROOT / 'cache/llm' / (key + '.json')
    if not path.exists():
        raise RuntimeError('Original parsed generation missing; no API fallback')
    return json.loads(path.read_text()), 'original_parsed_generation_cache'


def revalidate(row, *, fields=None, reference=None, same_day=False):
    parsed, source = generation(row, reference)
    errors, normalizations = [], []
    checked = extract_v2.validate(row['question'], row['transcript'], parsed,
        errors=errors, normalizations=normalizations, fields=fields,
        question_key=row.get('question_key') or None, allow_same_day=same_day)
    checked, keywords, overrides = redflags_v2.apply_negation(row['transcript'], checked)
    flags = redflags_v2.detect(row['transcript'], checked, question=row['question'],
                              validation_errors=errors, keyword_info=keywords)
    return checked, errors, flags, dict(generation_source=source, normalizations=normalizations,
                                      negation_overrides=overrides)


def rescore_B(rows, old_sessions):
    clips = []
    for row in rows:
        checked, errors, flags, details = revalidate(row, same_day=row['question'] == 'P3')
        clip = {key: value for key, value in row.items() if key != 'session_scores_json'}
        for field in ['keyterms']:
            clip[field] = json.loads(clip[field]) if clip.get(field) not in (None, '') else None
        clip.update(extracted=checked, validation_errors=errors, red_flags=flags,
            invalid_llm_output=bool(errors), validation_errors_v1=json.loads(row['validation_errors']),
            red_flags_before_session_resolution=copy.deepcopy(flags), partA_details=details)
        clips.append(clip)
    resolved, sessions = [], []
    for old in old_sessions:
        group = [c for c in clips if (c['speaker'], c['session']) == (old['speaker'], old['session'])]
        group = redflags_v2.resolve_session(group)
        resolved.extend(group)
        record = B.assemble(group)
        truth = json.loads(old['truth_json'])
        sessions.append(dict(speaker=old['speaker'], session=old['session'], record=record,
            truth=truth, scores=scoring_v2.score_setB(record, truth)))
    summary = B.summary_rows(sessions, resolved)
    return resolved, sessions, summary


def rescore_C(rows, reference):
    output = []
    for source in rows:
        fields = reference['FIELDS'][source['question']]
        checked, errors, flags, details = revalidate(source, fields=fields, reference=reference)
        # Each C clip is independent; never borrow another C card's P4 denial.
        item = checked[C.PRIMARY[source['question']]]
        status = 'needs_check' if source['question'] == 'P4' and flags['status'] == 'needs_check' else item['status']
        truth = dict(clip_id=source['clip'], question=source['question'],
            expected_status=source['expected_status'], expected_value=json.loads(source['expected_value']),
            expected_red_flag=source['expected_red_flag'])
        row = dict(source)
        row.update(extracted_json=json.dumps(checked, ensure_ascii=False), status=status,
            validation_error=json.dumps(errors, ensure_ascii=False) if errors else '',
            red_flag='yes' if flags['alert'] else 'no', red_flag_status=flags['status'],
            keyword_flags=json.dumps(flags['keyword_flags'], ensure_ascii=False),
            llm_flags=json.dumps(flags['llm_flags'], ensure_ascii=False),
            negated_keyword_flags=json.dumps(flags['negated_keyword_flags'], ensure_ascii=False),
            validation_error_v1=source['validation_error'], partA_details=json.dumps(details, ensure_ascii=False),
            **scoring_v2.score_setC(truth, checked, flags))
        output.append(row)
    return output, C.summarize(output)


def compare_B(previous, current):
    old = {(r['speaker'], r['field']): r for r in previous}
    return [dict(speaker=r['speaker'], field=r['field'],
        v1=f"{old[(r['speaker'], r['field'])]['correct']}/{old[(r['speaker'], r['field'])]['total']}",
        v2=f"{r['correct']}/{r['total']}",
        silently_wrong_v1=old[(r['speaker'], r['field'])]['silently_wrong'], silently_wrong_v2=r['silently_wrong'],
        safe_miss_v1=old[(r['speaker'], r['field'])]['safe_miss'], safe_miss_v2=r['safe_miss']) for r in current]


def compare_C(previous, current):
    old = {(r['condition'], r['speaker']): r for r in previous}
    metrics = [('status', 'status_correct', 'status_total'), ('value', 'value_correct', 'value_total'),
               ('red_flags_caught', 'red_flags_caught', 'red_flags_total'),
               ('false_alarms', 'false_alarms', 'false_alarm_total')]
    result = []
    for r in current:
        baseline = old[(r['condition'], r['speaker'])]
        for label, numerator, denominator in metrics:
            result.append(dict(condition=r['condition'], speaker=r['speaker'], metric=label,
                v1=f'{baseline[numerator]}/{baseline[denominator]}', v2=f'{r[numerator]}/{r[denominator]}'))
        for label in ['silently_wrong', 'safe_miss', 'needs_check', 'clips_with_invalid_fields']:
            result.append(dict(condition=r['condition'], speaker=r['speaker'], metric=label,
                               v1=baseline[label], v2=r[label]))
    return result


def flatten(row):
    return {k: json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in row.items()}


def main():
    output = ROOT / 'eval/results'
    targets = ['setB_per_clip_v2.csv', 'setB_per_session_v2.csv', 'setB_summary_v2.csv',
               'setC_per_clip_v2.csv', 'setC_summary_v2.csv', 'setB_comparison_v1_v2.csv',
               'setC_comparison_v1_v2.csv', 'partA_audit_v2.json']
    if any((output / name).exists() for name in targets):
        raise RuntimeError('Part A v2 outputs already exist; refusing silent overwrite')
    protected = [p for p in output.rglob('*') if p.is_file()]
    protected += [ROOT / name for name in ['extract.py', 'redflags.py', 'llm.py', 'gnani.py', 'meds.py',
        'eval/run_setB.py', 'eval/run_setC.py', 'data/setB_ground_truth.csv', 'data/setC_ground_truth.csv',
        'data/medicines.txt', 'data/symptoms.txt', 'prompts.yaml', 'eval/setB_full_v1_protocol.json',
        'eval/setC_development_v2_protocol.json']]
    before = {str(p.relative_to(ROOT)): digest(p) for p in protected}
    reference = original_setC_settings()
    with patch('requests.request', side_effect=AssertionError('Part A forbids network calls')), \
         patch('requests.post', side_effect=AssertionError('Part A forbids network calls')), \
         patch('llm.complete_json', side_effect=AssertionError('Part A forbids LLM calls')), \
         patch('gnani.stt', side_effect=AssertionError('Part A forbids STT calls')):
        clips, sessions, summary_B = rescore_B(read_csv(output / 'setB_per_clip.csv'), read_csv(output / 'setB_per_session.csv'))
        rows_C, summary_C = rescore_C(read_csv(output / 'setC_per_clip.csv'), reference)
    comparisons_B = compare_B(read_csv(output / 'setB_summary.csv'), summary_B)
    comparisons_C = compare_C(read_csv(output / 'setC_summary.csv'), summary_C)
    assert len(clips) == 212 and len(sessions) == 20 and len(rows_C) == 48
    session_lookup = {(s['speaker'], s['session']): s for s in sessions}
    clip_rows = []
    for clip in clips:
        row = flatten(clip)
        row['session_scores_json'] = json.dumps(session_lookup[(clip['speaker'], clip['session'])]['scores'], ensure_ascii=False)
        clip_rows.append(row)
    session_rows = [dict(speaker=s['speaker'], session=s['session'], record_json=json.dumps(s['record'], ensure_ascii=False),
        truth_json=json.dumps(s['truth'], ensure_ascii=False), scores_json=json.dumps(s['scores'], ensure_ascii=False),
        complete_truth=s['scores']['complete_truth'], complete_record_correct=s['scores']['complete_record_correct']) for s in sessions]
    for name, rows in [('setB_per_clip_v2.csv', clip_rows), ('setB_per_session_v2.csv', session_rows),
        ('setB_summary_v2.csv', summary_B), ('setC_per_clip_v2.csv', rows_C), ('setC_summary_v2.csv', summary_C),
        ('setB_comparison_v1_v2.csv', comparisons_B), ('setC_comparison_v1_v2.csv', comparisons_C)]:
        B.write_csv(output / name, rows)
    changed = [name for name, expected in before.items() if digest(ROOT / name) != expected]
    if changed:
        raise RuntimeError('Protected v1 files changed: ' + str(changed))
    audit = {'phase': 'Part A code-only v2', 'api_calls': {'Prisma': 0, 'Groq': 0},
        'v1_files_unchanged': True, 'v1_sha256': before,
        'source_generations_B': dict(__import__('collections').Counter(c['partA_details']['generation_source'] for c in clips)),
        'source_generations_C': dict(__import__('collections').Counter(json.loads(c['partA_details'])['generation_source'] for c in rows_C)),
        'v2_source_sha256': {name: digest(ROOT / name) for name in ['extract_v2.py', 'redflags_v2.py',
            'eval/scoring_v2.py', 'eval/rescore_partA_v2.py', 'eval/SCORING_NOTES.md']}}
    (output / 'partA_audit_v2.json').write_text(json.dumps(audit, indent=2) + '\n')
    for r in comparisons_B:
        if r['field'] in {'complaint', 'allergies', 'followups', 'red_flags_caught', 'false_alarms', 'complete_record', 'invalid_llm_output'}:
            print('B ' + json.dumps(r), flush=True)
    for r in comparisons_C:
        print('C ' + json.dumps(r), flush=True)
    print('Part A finished: 0 Prisma calls, 0 Groq calls; protected v1 files unchanged.')
    print('STOP before Part B prompt work or paid calls.')


if __name__ == '__main__':
    main()
