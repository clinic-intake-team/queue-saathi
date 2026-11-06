#!/usr/bin/env python3
"""Live Groq example checks only. No Prisma; paced with up to five retries."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import extract
import llm
import redflags
from eval.run_meds import normalize
from scripts.test_setB_stage2_examples import EXAMPLES


def matches(result, expected):
    problems = []
    for field, target in expected.items():
        actual = result[field]
        if actual['status'] != target['status']:
            problems.append(f'{field}: expected status {target["status"]}, got {actual["status"]}')
        if field == 'correction' and target['value'] is not None:
            value = actual['value']
            good = isinstance(value, str) and '20' in normalize(value).split()
        elif field in {'conditions', 'red_flag_symptoms'} and isinstance(actual['value'], list):
            good = sorted(actual['value']) == sorted(target['value'])
        else:
            good = actual['value'] == target['value']
        if not good:
            problems.append(f'{field}: expected {target["value"]!r}, got {actual["value"]!r}')
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real', action='store_true')
    parser.add_argument('--examples', nargs='+', type=int, choices=range(1, 9), default=list(range(1, 9)))
    args = parser.parse_args()
    if not args.real:
        parser.error('Explicit --real required: makes 8 Groq calls and no Prisma calls')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = extract.ROOT / 'examples' / ('stage2_live_' + stamp)
    output.mkdir(parents=True, exist_ok=False)
    _, model = llm.settings()
    rows = []
    for index, (question, transcript, key, expected) in enumerate(EXAMPLES, 1):
        if index not in args.examples:
            continue
        raw_path = output / f'{index:02d}_raw_response.json'
        errors = []
        try:
            parsed, raw = llm.complete_json([
                {'role': 'system', 'content': extract.SYSTEM_PROMPT},
                {'role': 'user', 'content': json.dumps({'question': question,
                    'fields': extract.FIELDS[question], 'question_key': key,
                    'transcript': transcript}, ensure_ascii=False)}],
                allow_real=True, raw_response_path=raw_path)
        except (ValueError, KeyError, IndexError, TypeError):
            if not raw_path.exists():
                raise
            raw = extract._raw_from_file(raw_path)
            parsed = None
        result = extract.validate(question, transcript, parsed, errors=errors, question_key=key)
        flags = redflags.detect(transcript, result, question=question, validation_errors=errors)
        problems = matches(result, expected)
        expected_alert = index == 3
        if flags['alert'] != expected_alert:
            problems.append(f'Expected alert={expected_alert}, got {flags["alert"]}')
        row = dict(index=index, question=question, question_key=key, transcript=transcript,
                   model=model, extracted=result, red_flags=flags,
                   invalid_llm_output=bool(errors), validation_errors=errors,
                   expected=expected, failures=problems, passed=not errors and not problems,
                   raw_response=raw)
        rows.append(row)
        (output / 'results.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({k: v for k, v in row.items() if k not in {'raw_response', 'expected'}}, ensure_ascii=False), flush=True)
    print(f'Passed {sum(r["passed"] for r in rows)}/{len(rows)}; invalid_llm_output {sum(r["invalid_llm_output"] for r in rows)}/{len(rows)}', flush=True)
    (output / 'rate_limits.json').write_text(json.dumps(llm.rate_limits(), indent=2) + '\n')
    print('Rate limits: ' + json.dumps(llm.rate_limits()), flush=True)
    print('212-call estimate: ' + json.dumps(llm.estimate_seconds(212)), flush=True)
    print('Saved: ' + str(output / 'results.json'), flush=True)


if __name__ == '__main__':
    main()
