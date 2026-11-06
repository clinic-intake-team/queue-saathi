#!/usr/bin/env python3
"""Isolated low-effort Set C comparison to frozen development run 2. Never calls Prisma."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gnani
import llm

ROOT = gnani.ROOT


def reference_modules():
    snapshot = json.loads((ROOT / 'eval/setC_development_v2_protocol.json').read_text())
    sources = {}
    reference_ref = json.loads((ROOT / 'eval/setC_reasoning_reference.json').read_text())['git_commit']
    for name in ['extract.py', 'redflags.py']:
        source = subprocess.run(['git', 'show', reference_ref + ':' + name], cwd=ROOT,
                                capture_output=True, check=True).stdout
        if hashlib.sha256(source).hexdigest() != snapshot['files'][name]:
            raise RuntimeError('Pinned commit does not contain the frozen run-2 reference: ' + name)
        sources[name] = source
        module = types.ModuleType(name[:-3])
        module.__file__ = str(ROOT / name)
        sys.modules[name[:-3]] = module
        exec(compile(source, 'frozen_run2/' + name, 'exec'), module.__dict__)
    extraction = sys.modules['extract']
    original_cache_path = extraction.cache_path
    def low_cache_path(question, transcript):
        original = original_cache_path(question, transcript)
        namespace = json.dumps({'original': original.stem, 'reasoning_effort': llm.reasoning_effort(),
                               'reference_extract_sha256': snapshot['files']['extract.py']}, sort_keys=True)
        return original.with_name(hashlib.sha256(namespace.encode()).hexdigest() + '.json')
    extraction.cache_path = low_cache_path
    evaluation = importlib.import_module('eval.run_setC')
    def verify_reference():
        for name, expected in snapshot['files'].items():
            if name in {'extract.py', 'redflags.py', 'llm.py'}:
                continue  # Extraction/flags use the verified frozen sources; provider is the new effort-aware client.
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
                raise RuntimeError('Set C run-2 input/scoring changed: ' + name)
        if snapshot['model'] != llm.settings()[1]:
            raise RuntimeError('Model changed relative to run 2')
    evaluation.verify_build = verify_reference
    return extraction, sys.modules['redflags'], evaluation, snapshot


def summary_comparison(previous, current):
    old = {(r['condition'], r['speaker']): r for r in previous}
    comparisons = []
    for row in current:
        reference = old[(row['condition'], row['speaker'])]
        comparisons.append(dict(condition=row['condition'], speaker=row['speaker'],
            status_run2=f"{reference['status_correct']}/{reference['status_total']}", status_low=f"{row['status_correct']}/{row['status_total']}",
            value_run2=f"{reference['value_correct']}/{reference['value_total']}", value_low=f"{row['value_correct']}/{row['value_total']}",
            flags_run2=f"{reference['red_flags_caught']}/{reference['red_flags_total']}", flags_low=f"{row['red_flags_caught']}/{row['red_flags_total']}",
            false_alarms_run2=f"{reference['false_alarms']}/{reference['false_alarm_total']}", false_alarms_low=f"{row['false_alarms']}/{row['false_alarm_total']}",
            silently_wrong_run2=int(reference['silently_wrong']), silently_wrong_low=row['silently_wrong'],
            safe_miss_run2=int(reference['safe_miss']), safe_miss_low=row['safe_miss'],
            invalid_run2=int(reference['clips_with_invalid_fields']), invalid_low=row['clips_with_invalid_fields']))
    return comparisons


def run(*, allow_real=False):
    if llm.reasoning_effort() != 'low':
        raise RuntimeError('This experiment requires LLM_REASONING_EFFORT=low')
    extraction, flags_module, evaluation, snapshot = reference_modules()
    paths, truth, prompts, medicines = evaluation.inputs()
    tasks = list(evaluation.tasks(paths, truth, medicines, evaluation.symptom_terms()))
    jobs = []
    seen = set()
    misses = 0
    for condition, path, speaker, clip, question, keyterms in tasks:
        cache = gnani.stt_cache_path(path, keyterms, context=prompts[question], mock=False)
        if not cache.exists():
            raise RuntimeError('Required Prisma cache missing: ' + path.name + ' ' + condition + '; no calls made')
        transcript = evaluation._cached_transcript(cache)
        key = extraction.cache_path(question, transcript)
        if key not in seen and not extraction.cached_available(question, transcript):
            misses += 1
        seen.add(key)
        jobs.append((condition, path, speaker, clip, question, transcript))
    print(f'Set C low-effort plan: {len(jobs)} rows, 0 Prisma calls, {misses} new Groq calls, other rows use LLM cache.', flush=True)
    if not allow_real:
        return
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = ROOT / 'eval/results' / ('setC_reasoning_low_' + stamp)
    destination.mkdir(parents=True, exist_ok=False)
    baseline_path = ROOT / 'eval/results/setC_summary.csv'
    previous = list(csv.DictReader(baseline_path.open()))
    (destination / 'run2_summary.csv').write_bytes(baseline_path.read_bytes())
    protocol = {'experiment': 'Set C frozen run-2 pipeline with reasoning_effort=low',
                'model': llm.settings()[1], 'reasoning_effort': 'low',
                'run2_protocol': snapshot,
                'provider_sha256': hashlib.sha256((ROOT / 'llm.py').read_bytes()).hexdigest(),
                'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'baseline_summary_sha256': hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
                'prisma_calls': 0, 'planned_groq_calls': misses}
    (destination / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    before = llm.STATS['real_calls']
    log_before = len(evaluation._log_rows(ROOT / 'logs/llm_calls.csv'))
    rows = []
    for condition, path, speaker, clip, question, transcript in jobs:
        details = {}
        result = extraction.extract(question, transcript, allow_real=True, details=details)
        errors = details.get('validation_errors', [])
        flags = flags_module.detect(transcript, result, question=question, validation_errors=errors)
        primary = result[evaluation.PRIMARY[question]]
        status = 'needs_check' if question == 'P4' and flags['status'] == 'needs_check' else primary['status']
        target = truth[clip]
        row = dict(speaker=speaker, clip=clip, question=question, condition=condition,
            transcript=transcript, status=status, extracted_json=json.dumps(result, ensure_ascii=False),
            validation_error=json.dumps(errors, ensure_ascii=False) if errors else '',
            raw_llm_response=json.dumps(details.get('raw_response'), ensure_ascii=False),
            red_flag='yes' if flags['alert'] else 'no', red_flag_status=flags['status'],
            expected_status=target['expected_status'], expected_value=json.dumps(target['expected_value']),
            expected_red_flag=target['expected_red_flag'], **evaluation.score(target, result, flags))
        rows.append(row)
        evaluation._write_csv(destination / 'setC_per_clip_low.csv', rows)
        if len(rows) % 10 == 0 or len(rows) == len(jobs):
            print(f'Set C progress {len(rows)}/{len(jobs)}; Groq attempts {llm.STATS["real_calls"] - before}; Prisma calls 0', flush=True)
    summary = evaluation.summarize(rows)
    comparison = summary_comparison(previous, summary)
    evaluation._write_csv(destination / 'setC_summary_low.csv', summary)
    evaluation._write_csv(destination / 'setC_comparison_run2_vs_low.csv', comparison)
    logs = evaluation._log_rows(ROOT / 'logs/llm_calls.csv')[log_before:]
    tokens = [int(r['tokens']) for r in logs if r['status'] == '200' and r['tokens']]
    audit = dict(status='complete', prisma_calls=0, groq_attempts=llm.STATS['real_calls'] - before,
                 successful_groq_calls=len(tokens), total_tokens=sum(tokens),
                 average_tokens=sum(tokens)/len(tokens) if tokens else 0,
                 projected_tokens_212=212*sum(tokens)/len(tokens) if tokens else 0)
    (destination / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    for row in comparison:
        print(json.dumps(row), flush=True)
    print(json.dumps(audit), flush=True)
    print('Saved comparison: ' + str(destination), flush=True)
    print('STOP: no Set B results discarded and no Set B restart performed.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real', action='store_true')
    args = parser.parse_args()
    run(allow_real=args.real)
