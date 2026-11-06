#!/usr/bin/env python3
"""Resume official v1: prepare all STT, then reuse/extract LLM. Hide partial scores."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import extract
import gnani
import llm
import redflags
from eval import run_setB as base

ROOT = gnani.ROOT


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extraction_semantics(source):
    tree = ast.parse(source)
    tree.body = [n for n in tree.body if not isinstance(n, ast.FunctionDef) or n.name != 'cache_path']
    return ast.dump(tree, include_attributes=False)


def verify_resume(paths):
    original_path = ROOT / 'eval/setB_full_v1_protocol.json'
    original = json.loads(original_path.read_text())
    if llm.settings()[1] != original['model'] or llm.reasoning_effort() != 'medium':
        raise RuntimeError('Must retain original GPT-OSS model and medium reasoning')
    for name, expected in original['files'].items():
        if name not in {'extract.py', 'llm.py'} and digest(ROOT / name) != expected:
            raise RuntimeError('Original scoring/input changed: ' + name)
    for name, expected in original['audio'].items():
        if digest(ROOT / name) != expected:
            raise RuntimeError('Original audio changed: ' + name)
    reference = ROOT / 'eval/setB_v1_extract_reference.py'
    if digest(reference) != original['files']['extract.py']:
        raise RuntimeError('Original extraction reference is not verified')
    if extraction_semantics(reference.read_text()) != extraction_semantics((ROOT / 'extract.py').read_text()):
        raise RuntimeError('Extraction prompt/validation changed beyond cache identity')
    overlay = {'parent_protocol_hash': digest(original_path), 'model': original['model'],
        'reasoning_effort': 'medium', 'semantics_verified_against_original': True,
        'operational_files': {name: digest(ROOT / name) for name in
                              ['llm.py', 'extract.py', 'eval/resume_setB_v1.py']}}
    target = ROOT / 'eval/setB_v1_resume_operations_portable.json'
    if target.exists() and json.loads(target.read_text()) != overlay:
        raise RuntimeError('Resume operational protocol differs; review before continuing')
    if not target.exists():
        target.write_text(json.dumps(overlay, indent=2) + '\n')
    return digest(original_path)


def cached_transcript(cache):
    value = json.loads(cache.read_text()).get('transcript')
    if not isinstance(value, str):
        raise RuntimeError('Invalid cached Prisma response; no call repeated automatically')
    return value


def finalize(paths, truth, clips, save):
    if len(clips) != len(paths) or {c['file'] for c in clips} != {p.relative_to(ROOT).as_posix() for p in paths}:
        raise RuntimeError('Refusing partial scoring')
    sessions = []
    for (speaker, session), target in truth.items():
        group = [c for c in clips if c['speaker'] == speaker and c['session'] == session]
        record = base.assemble(group)
        sessions.append(dict(speaker=speaker, session=session, record=record, truth=target,
                             scores=base.score_session(record, target)))
    summaries = base.summary_rows(sessions, clips)
    by_session = {(s['speaker'], s['session']): s for s in sessions}
    clip_csv = []
    for clip in clips:
        row = {k: base.dumps(v) if isinstance(v, (dict, list)) else v for k, v in clip.items()}
        row['session_scores_json'] = base.dumps(by_session[(clip['speaker'], clip['session'])]['scores'])
        clip_csv.append(row)
    session_csv = [dict(speaker=s['speaker'], session=s['session'], record_json=base.dumps(s['record']),
        truth_json=base.dumps(s['truth']), scores_json=base.dumps(s['scores']),
        complete_truth=s['scores']['complete_truth'], complete_record_correct=s['scores']['complete_record_correct']) for s in sessions]
    output = ROOT / 'eval/results'
    for label, rows in [('per_clip', clip_csv), ('per_session', session_csv), ('summary', summaries)]:
        base.write_csv(output / ('setB_' + label + '.csv'), rows)
    save('complete')
    for row in summaries:
        accuracy = f"{row['accuracy']:.1%}" if row['accuracy'] != '' else 'n.a.'
        print(f"{row['speaker']:7} {row['field']:40} {row['correct']}/{row['total']} ({accuracy})")
    base.print_failures(sessions, clips)
    return clips, sessions, summaries


def run(paths, truth, prompts, medicines, symptoms, *, allow_real=False):
    if not allow_real:
        raise RuntimeError('Explicit --real required for resume')
    protocol_hash = verify_resume(paths)
    if any((ROOT / f'eval/results/setB_{name}.csv').exists() for name in ['per_clip', 'per_session', 'summary']):
        raise RuntimeError('Official output exists; never overwrite it')
    checkpoint = ROOT / 'cache/setB_full_v1_checkpoint.json'
    saved = json.loads(checkpoint.read_text())
    if saved['protocol_hash'] != protocol_hash:
        raise RuntimeError('Checkpoint is not the original official v1')
    clips = saved['clips']
    completed = {c['file'] for c in clips}
    if len(completed) != len(clips):
        raise RuntimeError('Duplicate checkpoint clip')
    specs = {p: base.request_spec(p, prompts, medicines, symptoms) for p in paths}
    caches = {p: gnani.stt_cache_path(p, s['keyterms'], context=s['context'], mock=False) for p, s in specs.items()}
    prepared = {p for p, cache in caches.items() if cache.exists()}
    for p in prepared:
        cached_transcript(caches[p])
    initial_skips = len(prepared)
    before_stt, before_llm = gnani.STATS['real_calls'], llm.STATS['real_calls']
    # One in-flight Prisma response was cached after the old completed-clip checkpoint.
    # The original preflight had zero STT hits; account for that response without repeating it.
    prior = dict(saved.get('calls_made', {'prisma': 0, 'groq': 0}))
    prior['prisma'] = max(prior['prisma'], len({str(caches[p]) for p in prepared}))
    prior_elapsed = saved.get('elapsed_seconds', 0)
    start = time.monotonic()
    phase = 'prisma'
    llm_skips = len(completed)
    pending = None

    def progress():
        return {'phase': phase, 'stt_ready': len(prepared), 'completed_extractions': len(clips),
                'total_clips': len(paths), 'elapsed_seconds': round(prior_elapsed + time.monotonic() - start, 1),
                'calls_this_resume': {'prisma': gnani.STATS['real_calls'] - before_stt,
                                      'groq': llm.STATS['real_calls'] - before_llm},
                'calls_made': {'prisma': prior['prisma'] + gnani.STATS['real_calls'] - before_stt,
                               'groq': prior['groq'] + llm.STATS['real_calls'] - before_llm},
                'skipped_thanks_to_cache': {'prisma': initial_skips, 'groq_or_checkpoint': llm_skips}}

    def save(status, stop=None):
        value = {'protocol_hash': protocol_hash, 'clips': clips, 'status': status,
                 **progress(), 'stop': stop}
        tmp = checkpoint.with_suffix('.tmp')
        tmp.write_text(base.dumps(value))
        tmp.replace(checkpoint)

    def add_clip(path, result, details):
        nonlocal llm_skips
        spec = specs[path]
        transcript = cached_transcript(caches[path])
        errors = details.get('validation_errors', [])
        flags = redflags.detect(transcript, result, question=spec['question'], validation_errors=errors) if spec['question'] in {'P2', 'P4', 'F'} else dict(alert=False, status='not_screened', keyword_flags=[], llm_flags=[])
        clips.append(dict(**spec, file=path.relative_to(ROOT).as_posix(), transcript=transcript,
            extracted=result, validation_errors=errors, invalid_llm_output=bool(errors),
            raw_llm_response=details.get('raw_response'), red_flags=flags,
            processed_at=datetime.now(timezone.utc).isoformat()))
        completed.add(path.relative_to(ROOT).as_posix())
        save('running')
        if len(clips) % 10 == 0 or len(clips) == len(paths):
            print('PROGRESS ' + base.dumps(progress()), flush=True)

    def extract_one(path, real):
        spec = specs[path]
        details = {}
        result = extract.extract(spec['question'], cached_transcript(caches[path]),
            question_key=spec['question_key'], allow_same_day=spec['question'] == 'P3',
            allow_real=real, details=details)
        add_clip(path, result, details)

    original_mock, original_real = os.environ.get('GNANI_MOCK'), gnani._REAL_SCRIPT
    try:
        os.environ['GNANI_MOCK'] = '0'
        gnani._REAL_SCRIPT = True
        print('RESUME ' + base.dumps(progress()), flush=True)
        # Phase 1 finishes ALL remaining Prisma work before attempting any Groq call.
        for path in paths:
            if path in prepared:
                continue
            spec = specs[path]
            response = gnani.stt(path, keyterms=spec['keyterms'], context=spec['context'])
            if not isinstance(response.get('transcript'), str):
                raise RuntimeError('Prisma response has no transcript; no invalid LLM output fabricated')
            prepared.add(path)
            save('preparing_prisma')
            if len(prepared) % 10 == 0 or len(prepared) == len(paths):
                print('PROGRESS ' + base.dumps(progress()), flush=True)
        phase = 'groq_cache'
        save('prisma_complete')
        # Reuse every available original-effort extraction, even if an earlier uncached
        # clip may later receive a daily-limit HTTP 429.
        for path in paths:
            if path.relative_to(ROOT).as_posix() in completed:
                continue
            spec = specs[path]
            if extract.cached_available(spec['question'], cached_transcript(caches[path]),
                    question_key=spec['question_key'], allow_same_day=spec['question'] == 'P3'):
                llm_skips += 1
                extract_one(path, False)
        phase = 'groq'
        for path in paths:
            if path.relative_to(ROOT).as_posix() in completed:
                continue
            pending = path.relative_to(ROOT).as_posix()
            spec = specs[path]
            # A preceding identical question/transcript may have populated this key.
            hit = extract.cached_available(spec['question'], cached_transcript(caches[path]),
                question_key=spec['question_key'], allow_same_day=spec['question'] == 'P3')
            if hit:
                llm_skips += 1
            extract_one(path, True)
        return finalize(paths, truth, clips, save)
    except llm.DailyQuotaError as exc:
        reset = datetime.fromtimestamp(exc.reset_at, timezone.utc) if exc.reset_at else None
        stop = {'reason': str(exc), 'pending_clip': pending, 'quota': exc.quota,
                'quota_reset_utc': reset.isoformat() if reset else None,
                'quota_reset_ist': reset.astimezone(ZoneInfo('Asia/Kolkata')).isoformat() if reset else None,
                'server_message': exc.server_message, 'wait_seconds': exc.wait_seconds, 'wait_hint': exc.wait_hint,
                'resume_command': '.venv/bin/python eval/resume_setB_v1.py --real'}
        save('daily_quota_stopped', stop)
        print('CLEAN STOP ' + base.dumps({**progress(), **stop}), flush=True)
        print('Groq daily-limit message: ' + (exc.server_message or str(exc)), flush=True)
        print('Groq wait time: ' + str(exc.wait_hint or exc.wait_seconds or 'not provided'), flush=True)
        print('Daily-token reset: ' + (stop['quota_reset_ist'] or 'UNKNOWN — Groq did not return daily-token reset information.'), flush=True)
        print('No partial scores or per-clip results printed; all progress and Prisma caches retained.', flush=True)
        return None
    finally:
        if original_mock is None:
            os.environ.pop('GNANI_MOCK', None)
        else:
            os.environ['GNANI_MOCK'] = original_mock
        gnani._REAL_SCRIPT = original_real


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real', action='store_true')
    args = parser.parse_args()
    paths, truth, prompts, medicines, symptoms = base.load_inputs()
    verify_resume(paths)
    if not args.real:
        print('Dry verification only. Use --real for the already-approved resume.')
        return
    run(paths, truth, prompts, medicines, symptoms, allow_real=True)


if __name__ == '__main__':
    main()
