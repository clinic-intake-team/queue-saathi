#!/usr/bin/env python3
"""Full 212-clip Set B replay. Offline preflight by default; explicit paid-call gate."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml
import extract
import gnani
import llm
import meds
import redflags
from eval.run_meds import normalize

ROOT = gnani.ROOT
FOLLOWUP_COUNT = {1: 2, 2: 3, 3: 2, 4: 2, 5: 1, 6: 1, 7: 2, 8: 2, 9: 0, 10: 1}
FOLLOWUP_KEYS = {1: ['measured', 'chills'], 2: ['last_bp', 'pain_location', 'pain_score'],
                 3: ['pain_location', 'pain_score'], 4: ['phlegm', 'breathless'],
                 5: ['frequency_per_day'], 6: ['last_sugar'],
                 7: ['pain_location', 'pain_score'], 8: ['pain_location', 'pain_score'],
                 9: [], 10: ['measured']}
FOLLOWUP_PROMPTS = {
    'measured': 'Bukhaar naapa tha? Kitna tha?', 'chills': 'Thand lag ke aata hai?',
    'last_bp': 'Pichhli baar BP kitna aaya tha?', 'pain_location': 'Dard theek kahan hai?',
    'pain_score': 'Ek se das mein dard kitna tez hai?', 'phlegm': 'Balgam aata hai? Kis rang ka?',
    'breathless': 'Saans phoolti hai?', 'frequency_per_day': 'Din mein kitni baar ulti ya dast ho rahe hain?',
    'last_sugar': 'Pichhli baar sugar kitni aayi thi?'}
R1_PROMPT = 'Maine jo dawaiyon ke naam dohraye hain, kya woh sahi hain?'
JSON_TRUTH = {'complaint_symptoms', 'duration_days', 'follow_up_facts', 'medicines', 'allergies', 'conditions'}
# Frozen BEFORE inspecting the replay's cached transcripts or generating scores.
CONCEPTS = {
    'fever': [r'fever|bukha+r|बुखार'],
    'body ache': [r'body (?:ache|pain)|(?:ache|pain).*body|badan.*dard|शरीर.*दर्द|बदन.*दर्द'],
    'BP check': [r'(?:bp|blood pressure).*(?:check|follow.?up|review)|(?:check|follow.?up|review).*(?:bp|blood pressure)|बीपी.*(?:चेक|जांच)'],
    'frequent headaches': [r'headache|head pain|sar.*dard|सिर.*दर्द', r'frequent|often|recurrent|regular|baar baar|बार.*बार'],
    'headache': [r'headache|head pain|sar.*dard|सिर.*दर्द'],
    'chest pain': [r'chest.*pain|pain.*chest|seene?.*dard|सीने.*दर्द'],
    'chest heaviness': [r'(?:chest|seene?|सीने).*(?:heav|pressure|bha+r|भारी|दबाव)|heav.*chest'],
    'cough': [r'cough|khaa?nsi|खांसी|खाँसी'],
    'loose motions': [r'loose (?:motion|stool)|diarrh[oe]+a|dast|दस्त'],
    'vomited once': [r'vomit|ulti|उल्टी', r'once|one (?:time|episode)|1 (?:time|episode)|ek baar|एक बार'],
    'sugar check': [r'(?:sugar|diabet\w*).*(?:check|follow.?up|review)|(?:check|follow.?up|review).*(?:sugar|diabet\w*)|शुगर.*(?:चेक|जांच)'],
    'fatigue': [r'fatigue|tired|weakness|kamzori|thak|कमजोरी|थक'],
    'knee pain': [r'knee.*pain|pain.*knee|ghutn.*dard|घुटन.*दर्द'],
    'left arm weakness': [r'left.*(?:arm|hand).*weak|weak.*left.*(?:arm|hand)|baa?y[ae].*(?:haath|hath).*(?:kamzor|weak)|बाएं.*(?:हाथ|बांह).*कमजोर'],
    'difficulty speaking': [r'(?:difficult|trouble|problem|slurr).*speak|speak.*(?:difficult|trouble|problem)|slurred speech|speech.*(?:difficult|problem)|bolne.*dikkat|बोलने.*दिक्कत'],
    'left arm': [r'left.*(?:arm|hand)|baa?y[ae].*(?:haath|hath)|बाएं.*(?:हाथ|बांह)'],
    'right knee': [r'right.*knee|daa?y[ae].*ghutn|दाएं.*घुटन'],
    'front of head': [r'front.*head|frontal|forehead|head.*front|maat[h]?|माथ|सिर.*आगे'],
    'back of head': [r'back.*head|head.*back|occipital|posterior.*head|sar.*pee?ch|सिर.*पीछे'],
    'near neck': [r'neck|nape|gardan|गर्दन'],
}


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def expected_rows(session):
    return ['P0', 'P1', 'P2', 'P3'] + [f'F{i}' for i in range(1, FOLLOWUP_COUNT[int(session[1:])] + 1)] + ['P4', 'P5', 'R1', 'P6', 'P7']


def classify(path):
    match = re.fullmatch(r'(ch|tm)_(S\d{2})_(P[0-7]|F[1-3]|R1)\.m4a', path.name)
    if not match or match[2] not in {f'S{i:02}' for i in range(1, 11)}:
        raise ValueError('Unexpected Set B recording: ' + path.name)
    return match.groups()


def followup_key(speaker, session, row):
    keys = list(FOLLOWUP_KEYS[int(session[1:])])
    # Original semantic filenames, preserved in the pre-copy SHA-256 inventory,
    # establish ch S03/S04 question order. Keep approved destination numbers intact.
    if speaker == 'ch' and session in {'S03', 'S04'}:
        keys.reverse()
    return keys[int(row[1:]) - 1]


def request_spec(path, prompts, medicines, symptoms):
    speaker, session, row = classify(path)
    question = 'F' if row.startswith('F') else row
    key = followup_key(speaker, session, row) if question == 'F' else None
    context = FOLLOWUP_PROMPTS[key] if key else (R1_PROMPT if row == 'R1' else prompts[row])
    terms = symptoms if question in {'P2', 'P4', 'F'} else (medicines if question in {'P5', 'R1'} else None)
    return dict(speaker=speaker, session=session, row=row, question=question,
                question_key=key, context=context, keyterms=terms)


def load_inputs():
    prompts = yaml.safe_load((ROOT / 'prompts.yaml').read_text())
    medicines = (ROOT / 'data/medicines.txt').read_text().splitlines()
    symptoms = (ROOT / 'data/symptoms.txt').read_text().splitlines()
    medicines, symptoms = [[s.strip() for s in values if s.strip()] for values in (medicines, symptoms)]
    if not all(0 < len(terms) <= 200 for terms in (medicines, symptoms)):
        raise ValueError('Keyterm arrays must contain 1–200 terms')
    truth = {}
    with (ROOT / 'data/setB_ground_truth.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            row = {k: json.loads(v) if k in JSON_TRUTH else v for k, v in row.items()}
            row['age'], row['token'] = int(row['age']), int(row['token'])
            key = (row['speaker'], row['session'])
            if key in truth:
                raise ValueError('Duplicate ground truth')
            truth[key] = row
    expected = {(sp, f'S{i:02}') for sp in ['ch', 'tm'] for i in range(1, 11)}
    if set(truth) != expected:
        raise ValueError('Expected 20 session truth rows')
    paths = list((ROOT / 'recordings').glob('*_S??_*'))
    with (ROOT / 'eval/setB_final_mapping.csv').open(newline='') as f:
        approved = {row['destination']: row for row in csv.DictReader(f)}
    groups = defaultdict(list)
    for path in paths:
        sp, session, row = classify(path)
        relative = path.relative_to(ROOT).as_posix()
        entry = approved.get(relative)
        if (not entry or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']
                or not 0 < float(entry['duration_seconds']) < 30):
            raise ValueError('Recording differs from approved mapping or duration: ' + relative)
        groups[(sp, session)].append(row)
    if set(groups) != expected or any(Counter(rows) != Counter(expected_rows(session)) for (_, session), rows in groups.items()):
        raise ValueError('Recordings must contain exactly 106 per speaker, with every expected row once')
    paths.sort(key=lambda p: (*classify(p)[:2], expected_rows(classify(p)[1]).index(classify(p)[2])))
    return paths, truth, prompts, medicines, symptoms


def protocol_files():
    return ['extract.py', 'llm.py', 'gnani.py', 'meds.py', 'redflags.py',
            'eval/run_setB.py', 'eval/SETB_SCORING_NOTES.md', 'data/setB_ground_truth.csv',
            'data/medicines.txt', 'data/symptoms.txt', 'prompts.yaml',
            'eval/setB_final_mapping.csv', 'eval/setB_file_inventory.csv']


def protocol_snapshot(paths):
    _, model = llm.settings()
    return {'protocol': 'full_setB_v1', 'model': model, 'temperature': 0,
            'response_format': {'type': 'json_object'},
            'files': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in protocol_files()},
            'audio': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}


def verify_protocol(paths):
    target = ROOT / 'eval/setB_full_v1_protocol.json'
    if not target.exists() or json.loads(target.read_text()) != protocol_snapshot(paths):
        raise RuntimeError('Frozen full Set B v1 protocol is missing or changed; do not run or overwrite results')


def call_plan(paths, prompts, medicines, symptoms):
    stt_seen, llm_seen = set(), set()
    counts = dict(recordings=len(paths), prisma_calls=0, prisma_cache_hits=0,
                  groq_known_calls=0, groq_cache_hits=0, groq_pending_transcripts=0)
    for path in paths:
        spec = request_spec(path, prompts, medicines, symptoms)
        cache = gnani.stt_cache_path(path, spec['keyterms'], context=spec['context'], mock=False)
        if cache.exists():
            counts['prisma_cache_hits'] += 1
            transcript = json.loads(cache.read_text())['transcript']
            if not isinstance(transcript, str):
                raise ValueError('Invalid cached transcript')
            key = extract.cache_path(spec['question'], transcript, question_key=spec['question_key'])
            if extract.cached_available(spec['question'], transcript, question_key=spec['question_key'], allow_same_day=spec['question'] == 'P3') or key in llm_seen:
                counts['groq_cache_hits'] += 1
            else:
                counts['groq_known_calls'] += 1
            llm_seen.add(key)
        elif cache in stt_seen:
            counts['prisma_cache_hits'] += 1
            # Its eventual transcript is unknown: this is an upper bound, not exact.
            counts['groq_pending_transcripts'] += 1
        else:
            counts['prisma_calls'] += 1
            counts['groq_pending_transcripts'] += 1
        stt_seen.add(cache)
    counts['groq_max_before_retries'] = counts['groq_known_calls'] + counts['groq_pending_transcripts']
    # Use the same reservation as the pacing code and the longest current prompt.
    reservation = llm._reservation({'messages': [{'role': 'system', 'content': extract.SYSTEM_PROMPT},
            {'role': 'user', 'content': 'x' * 600}]}, llm.rate_limits())
    counts['groq_time_estimate'] = llm.estimate_seconds(counts['groq_max_before_retries'], tokens_per_call=reservation)
    counts['212_groq_time_estimate'] = llm.estimate_seconds(212, tokens_per_call=reservation)
    print('SET B CALL-COUNT GATE — NO API CALLS MADE BY PREFLIGHT')
    print(dumps(counts))
    print('Prisma has up to 3 attempts/call; Groq up to 6 attempts/call (five retries).')
    print('Groq count for missing STT is an upper bound until transcripts exist; identical transcripts may share LLM cache.')
    print('S02 truth includes back of head OR near neck, pain score 5; complete-truth coverage 20/20 sessions.')
    print('Time estimate excludes Prisma time, response latency, other users of the organization and daily-limit waits.')
    return counts


def positive(text, pattern):
    for clause in re.split(redflags.BOUNDARY, text.lower()):
        for match in re.finditer(pattern, clause, re.I):
            if redflags._present(clause, match):
                return True
    return False


def concept_matches(value, concept):
    passages = [value['summary'], *value['symptoms']] if isinstance(value, dict) else [str(value)]
    return all(any(positive(p, pattern) for p in passages) for pattern in CONCEPTS[concept])


def envelope(value=None, status='unclear', evidence=''):
    return dict(value=value, status=status, evidence=evidence)


def measured_temperature(text):
    """Additional fact in a combined measured/temperature question, no LLM guessing."""
    normalized = normalize(text)
    celsius = re.search(r'(\d+(?:\.\d+)?)\s*(?:celsius|degree c|degrees c|c\b)', text, re.I)
    if celsius:
        return round(float(celsius[1]) * 9 / 5 + 32, 1)
    matches = re.findall(r'(?<!\w)(\d{2,3}(?:\.\d+)?)(?!\w)', text)
    if not matches:
        matches = re.findall(r'(?<!\w)(\d{2,3}(?:\.\d+)?)(?!\w)', normalized)
    plausible = [float(n) for n in matches if 80 <= float(n) <= 115]
    return plausible[0] if len(plausible) == 1 else None


def resolved_medicines(p5, r1, *, fuzzy):
    item = p5['extracted']['medicines']
    candidates = meds.parse(p5['transcript'], fuzzy=fuzzy)
    if item['status'] != 'ok':
        return dict(item), candidates
    confirmation = r1['extracted']['confirmed']
    correction = r1['extracted']['correction']
    if confirmation['status'] == 'ok' and confirmation['value'] is False:
        if correction['status'] != 'ok':
            return envelope(), candidates
        changed = meds.parse(correction['value'], fuzzy=fuzzy)
        if changed:
            candidates = changed
        elif len(candidates) == 1:
            # Only an explicit dose/strength correction with one candidate is unambiguous.
            text = normalize(correction['value'])
            numbers = re.findall(r'(?<!\w)\d+(?!\w)', text)
            if len(numbers) == 1 and re.search(r'dose|strength|mg|milligram|मिलीग्राम|डोज', text):
                candidates[0] = dict(candidates[0], strength=numbers[0],
                                     display=candidates[0]['name'] + ' ' + numbers[0])
            else:
                return envelope(), candidates
        else:
            return envelope(), candidates
    candidates = meds.apply_confirmation(candidates, r1['transcript'], r1['extracted'])
    # An extracted medicine not supported by the deterministic matcher is not silently accepted.
    if not candidates and item['value']:
        return envelope(), candidates
    return envelope([{'name': m['name'], 'strength': m['strength'], 'purpose': m['purpose']} for m in candidates], 'ok', item['evidence']), candidates


def assemble(clips):
    by_row = {c['row']: c for c in clips}
    record = {}
    for row, fields in [('P0', ['token']), ('P1', ['age', 'sex']), ('P2', ['complaint']),
                        ('P3', ['duration_days']), ('P6', ['allergies']), ('P7', ['conditions'])]:
        record.update({f: by_row[row]['extracted'][f] for f in fields})
    followups = {}
    for clip in clips:
        if clip['question'] != 'F':
            continue
        item = clip['extracted']['follow_up']
        key = clip['question_key']
        followups[key] = envelope(item['value']['value'], 'ok', item['evidence']) if item['status'] == 'ok' else dict(item)
        if key == 'measured' and item['status'] == 'ok' and item['value']['value'] is True:
            temperature = measured_temperature(clip['transcript'])
            followups['temperature_f'] = envelope(temperature, 'ok', clip['transcript']) if temperature is not None else envelope()
    record['followups'] = followups
    for fuzzy, field in [(False, 'medicines_raw'), (True, 'medicines')]:
        record[field], candidates = resolved_medicines(by_row['P5'], by_row['R1'], fuzzy=fuzzy)
        record[field + '_candidates'] = candidates
    record['medicine_confirmation'] = by_row['R1']['extracted']
    alerts = [c for c in clips if c['question'] in {'P2', 'P4', 'F'} and c['red_flags']['alert']]
    flag_status = 'needs_check' if any(c['red_flags']['status'] == 'needs_check' for c in alerts) else 'ok'
    record['red_flag'] = envelope(bool(alerts), flag_status, ' | '.join(c['transcript'] for c in alerts))
    record['red_flag_sources'] = [c['row'] for c in alerts]
    return record


def followup_correct(actual, expected, key):
    if isinstance(expected, dict) and set(expected) == {'min', 'max'}:
        return type(actual) in (int, float) and expected['min'] <= actual <= expected['max']
    if key == 'pain_location':
        options = expected if isinstance(expected, list) else [expected]
        return isinstance(actual, str) and any(concept_matches(actual, target) for target in options)
    if key == 'phlegm':
        if not isinstance(actual, dict) or actual.get('present') is not expected['present']:
            return False
        colour = str(actual.get('colour', '')).lower()
        return colour in {'yellow', 'yellowish', 'peela', 'pila', 'पीला', 'पीले'} if expected['colour'] == 'yellow' else colour == expected['colour']
    return type(actual) is type(expected) and actual == expected or (type(actual) in (int, float) and type(expected) in (int, float) and actual == expected)


def canonical_name(value):
    return normalize(value or '').replace(' ', '')


def medicine_counts(actual, expected):
    actual = actual if isinstance(actual, list) else []
    used = set()
    correct = strength_correct = 0
    for target in expected:
        match = None
        for index, candidate in enumerate(actual):
            if index in used:
                continue
            same = (canonical_name(candidate.get('name')) == canonical_name(target['name'])) if target['name'] else (
                candidate.get('name') is None and canonical_name(candidate.get('purpose')) == canonical_name(target['purpose']))
            if same:
                match = index
                break
        if match is not None:
            correct += 1
            used.add(match)
            if target['strength'] is not None and normalize(str(actual[match].get('strength') or '')) == normalize(target['strength']):
                strength_correct += 1
    total_strength = sum(m['strength'] is not None for m in expected)
    return dict(names_correct=correct, names_total=len(expected), strengths_correct=strength_correct,
                strengths_total=total_strength, extra_names=len(actual) - len(used))


def comparison(correct, item, expected):
    status = item.get('status', 'unclear')
    return dict(correct=int(correct), expected=expected, got=item.get('value'), status=status,
                silently_wrong=int(not correct and status == 'ok'),
                safe_miss=int(not correct and status in {'unclear', 'declined', 'needs_check'}))


def score_session(record, truth):
    scores = {}
    for field in ['token', 'age', 'sex', 'allergies', 'conditions']:
        item = record[field]
        expected = truth[field]
        equal = (sorted(canonical_name(v) for v in item['value']) == sorted(canonical_name(v) for v in expected)
                 if isinstance(item['value'], list) and isinstance(expected, list) else item['value'] == expected)
        scores[field] = comparison(item['status'] == 'ok' and equal, item, expected)
    item = record['complaint']
    good = item['status'] == 'ok' and all(concept_matches(item['value'], s) for s in truth['complaint_symptoms'])
    scores['complaint'] = comparison(good, item, truth['complaint_symptoms'])
    item = record['duration_days']
    target = truth['duration_days']
    targets = target if isinstance(target, list) else [target]
    scores['duration_days'] = comparison(item['status'] == 'ok' and item['value'] in targets, item, target)
    follow_scores = {}
    for key, expected in truth['follow_up_facts'].items():
        if expected is None:
            continue
        item = record['followups'].get(key, envelope())
        follow_scores[key] = comparison(item['status'] == 'ok' and followup_correct(item['value'], expected, key), item, expected)
    follow_good = all(s['correct'] for s in follow_scores.values())
    status = 'ok' if all(s['status'] == 'ok' for s in follow_scores.values()) else 'unclear'
    scores['followups'] = comparison(follow_good, envelope({k: s['got'] for k, s in follow_scores.items()}, status), {k: v for k, v in truth['follow_up_facts'].items() if v is not None})
    for field in ['medicines_raw', 'medicines']:
        item = record[field]
        counts = medicine_counts(item['value'], truth['medicines'])
        names_ok = item['status'] == 'ok' and counts['names_correct'] == counts['names_total'] and not counts['extra_names']
        scores[field + '_names'] = comparison(names_ok, item, truth['medicines'])
        scores[field + '_names_strengths'] = comparison(names_ok and counts['strengths_correct'] == counts['strengths_total'], item, truth['medicines'])
        scores[field + '_counts'] = counts
    item = record['red_flag']
    expected_flag = truth['red_flag'] == 'yes'
    scores['red_flag'] = comparison(item['value'] == expected_flag, item, expected_flag)
    # Raw matching is a baseline, not a requirement of the final assembled record.
    final = [v['correct'] for k, v in scores.items() if 'correct' in v and not k.startswith('medicines_raw')]
    coverage = all(v is not None for v in truth['follow_up_facts'].values())
    return dict(fields=scores, followup_fields=follow_scores,
                complete_truth=coverage, complete_record_correct=int(all(final)) if coverage else None)


def summary_rows(sessions, clips):
    output = []
    for speaker in ['overall', 'ch', 'tm']:
        group = [s for s in sessions if speaker == 'overall' or s['speaker'] == speaker]
        relevant_clips = [c for c in clips if speaker == 'overall' or c['speaker'] == speaker]
        invalid = sum(bool(c['validation_errors']) for c in relevant_clips)
        fields = [k for k, v in group[0]['scores']['fields'].items() if 'correct' in v] if group else []
        for field in fields:
            values = [s['scores']['fields'][field] for s in group]
            correct = sum(v['correct'] for v in values)
            output.append(dict(speaker=speaker, field=field, correct=correct, total=len(values),
                accuracy=correct / len(values) if values else '',
                silently_wrong=sum(v['silently_wrong'] for v in values), safe_miss=sum(v['safe_miss'] for v in values),
                invalid_llm_output_clips=invalid))
        follow_keys = sorted({k for s in group for k in s['scores']['followup_fields']})
        for key in follow_keys:
            values = [s['scores']['followup_fields'][key] for s in group if key in s['scores']['followup_fields']]
            n = sum(v['correct'] for v in values)
            output.append(dict(speaker=speaker, field='follow_up:' + key, correct=n, total=len(values),
                accuracy=n / len(values), silently_wrong=sum(v['silently_wrong'] for v in values),
                safe_miss=sum(v['safe_miss'] for v in values), invalid_llm_output_clips=invalid))
        for version in ['medicines_raw', 'medicines']:
            counts = [s['scores']['fields'][version + '_counts'] for s in group]
            for metric, numerator, denominator in [('per_medicine_names', 'names_correct', 'names_total'), ('per_medicine_name_strength', 'strengths_correct', 'strengths_total')]:
                n, d = sum(c[numerator] for c in counts), sum(c[denominator] for c in counts)
                output.append(dict(speaker=speaker, field=version + '_' + metric, correct=n, total=d, accuracy=n / d if d else '', silently_wrong='', safe_miss='', invalid_llm_output_clips=invalid))
        for label, positive_target in [('red_flags_caught', True), ('false_alarms', False)]:
            selected = [s for s in group if (s['truth']['red_flag'] == 'yes') is positive_target]
            n = sum(s['record']['red_flag']['value'] for s in selected)
            output.append(dict(speaker=speaker, field=label, correct=n, total=len(selected), accuracy=n / len(selected) if selected else '', silently_wrong='', safe_miss='', invalid_llm_output_clips=invalid))
        eligible = [s for s in group if s['scores']['complete_truth']]
        n = sum(s['scores']['complete_record_correct'] for s in eligible)
        output.append(dict(speaker=speaker, field='complete_record', correct=n, total=len(eligible), accuracy=n / len(eligible) if eligible else '', silently_wrong='', safe_miss='', invalid_llm_output_clips=invalid))
        output.append(dict(speaker=speaker, field='complete_truth_coverage', correct=len(eligible), total=len(group), accuracy=len(eligible) / len(group) if group else '', silently_wrong='', safe_miss='', invalid_llm_output_clips=invalid))
        output.append(dict(speaker=speaker, field='invalid_llm_output', correct=invalid, total=len(relevant_clips),
            accuracy=invalid / len(relevant_clips) if relevant_clips else '', silently_wrong='', safe_miss='', invalid_llm_output_clips=invalid))
    return output


def write_csv(path, rows):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    with temp.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(path)


def failure_cause(field, score, relevant):
    validation_field = ('medicines' if field.startswith('medicines') else
                        'follow_up' if field.startswith('follow') else field)
    if any(e.get('field') == validation_field for c in relevant for e in c['validation_errors']):
        return 'invalid output'
    transcript = ' '.join(c['transcript'] for c in relevant)
    if field == 'complaint':
        supported = all(concept_matches(transcript, v) for v in score['expected'])
    elif field.startswith('medicines'):
        counts = medicine_counts([{'name': m['name'], 'strength': m['strength'], 'purpose': m['purpose']} for m in meds.parse(transcript)], score['expected'])
        supported = counts['names_correct'] == counts['names_total'] and counts['strengths_correct'] == counts['strengths_total']
    elif field in {'age', 'token', 'duration_days'}:
        targets = score['expected'] if isinstance(score['expected'], list) else [score['expected']]
        supported = any(str(v) in normalize(transcript).split() for v in targets)
    elif field == 'red_flag':
        supported = bool(redflags.keyword_flags(transcript)) == score['expected']
    elif field == 'sex':
        pattern = r'\b(?:male|man|purush)\b|पुरुष' if score['expected'] == 'male' else r'\b(?:female|woman|mahila)\b|महिला'
        supported = bool(re.search(pattern, transcript, re.I))
    elif field in {'allergies', 'conditions'}:
        target = score['expected']
        if target == 'none':
            supported = bool(re.search(r'\b(?:no|none|not|nahi|nahin)\b|नहीं', transcript, re.I))
        elif target == 'unknown':
            supported = bool(re.search(r'pata nahi|don.t know|unknown|पता नहीं|मालूम नहीं', transcript, re.I))
        else:
            aliases = {'diabetes': r'diabet|sugar|शुगर|मधुमेह', 'BP': r'\bbp\b|blood pressure|बीपी',
                       'thyroid': r'thyroid|थायर', 'asthma': r'asthma|अस्थमा|दमा'}
            supported = all(bool(re.search(aliases.get(v, re.escape(v)), transcript, re.I)) for v in target)
    else:
        # Output needs human review if literal evidence/ground truth wording is ambiguous.
        return 'scoring'
    return 'extraction' if supported else 'STT'


def print_failures(sessions, clips):
    row_by_field = {'token': ['P0'], 'age': ['P1'], 'sex': ['P1'], 'complaint': ['P2'],
                    'duration_days': ['P3'], 'allergies': ['P6'], 'conditions': ['P7']}
    print('FAILED FIELDS — BOTH SPEAKERS (provisional transcript-based cause; no audio replay)')
    for session in sessions:
        group = [c for c in clips if c['speaker'] == session['speaker'] and c['session'] == session['session']]
        entries = list(session['scores']['fields'].items())
        entries += [('follow_up:' + k, v) for k, v in session['scores']['followup_fields'].items()]
        for field, score in entries:
            if 'correct' not in score or score['correct']:
                continue
            if field.startswith('medicines'):
                relevant = [c for c in group if c['row'] in {'P5', 'R1'}]
            elif field == 'red_flag':
                relevant = [c for c in group if c['question'] in {'P2', 'P4', 'F'}]
            elif field.startswith('follow'):
                key = field.split(':', 1)[-1]
                relevant = [c for c in group if c['question'] == 'F' and (field == 'followups' or c['question_key'] == key or key == 'temperature_f' and c['question_key'] == 'measured')]
            else:
                relevant = [c for c in group if c['row'] in row_by_field[field]]
            print(dumps(dict(speaker=session['speaker'], session=session['session'], field=field,
                row=[c['row'] for c in relevant], transcript=[c['transcript'] for c in relevant],
                expected=score['expected'], got=score['got'], cause=failure_cause(field, score, relevant))))


def run(paths, truth, prompts, medicines, symptoms, *, allow_real=False):
    if not allow_real:
        raise RuntimeError('Real run requires the explicit call-count confirmation gate')
    verify_protocol(paths)
    output = ROOT / 'eval/results'
    targets = [output / f'setB_{name}.csv' for name in ['per_clip', 'per_session', 'summary']]
    if any(p.exists() for p in targets):
        raise RuntimeError('Full v1 results already exist; never overwrite. A later run needs a separate v2 protocol.')
    checkpoint = ROOT / 'cache/setB_full_v1_checkpoint.json'
    protocol_hash = hashlib.sha256((ROOT / 'eval/setB_full_v1_protocol.json').read_bytes()).hexdigest()
    saved = json.loads(checkpoint.read_text()) if checkpoint.exists() else {'protocol_hash': protocol_hash, 'clips': []}
    if saved['protocol_hash'] != protocol_hash:
        raise RuntimeError('Checkpoint protocol differs')
    clips = saved['clips']
    completed = {c['file'] for c in clips}
    old_mock, old_real = os.environ.get('GNANI_MOCK'), gnani._REAL_SCRIPT
    before_stt, before_llm = gnani.STATS['real_calls'], llm.STATS['real_calls']
    llm_hits = 0
    started = time.monotonic()
    prior_elapsed = saved.get('elapsed_seconds', 0)
    prior_calls = saved.get('calls_made', {'prisma': 0, 'groq': 0})
    current_spec = None

    def progress():
        return {'completed_clips': len(clips), 'total_clips': len(paths),
                'elapsed_seconds': round(prior_elapsed + time.monotonic() - started, 1),
                'calls_made': {'prisma': prior_calls['prisma'] + gnani.STATS['real_calls'] - before_stt,
                               'groq': prior_calls['groq'] + llm.STATS['real_calls'] - before_llm}}

    def save_state(status, stop=None):
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        temp = checkpoint.with_suffix('.tmp')
        state = {'protocol_hash': protocol_hash, 'clips': clips, 'status': status,
                 **progress(), 'stop': stop}
        temp.write_text(dumps(state))
        temp.replace(checkpoint)

    print('Starting/resuming: ' + dumps(progress()), flush=True)
    try:
        os.environ['GNANI_MOCK'] = '0'
        gnani._REAL_SCRIPT = True
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            if relative in completed:
                continue
            spec = request_spec(path, prompts, medicines, symptoms)
            current_spec = spec
            response = gnani.stt(path, keyterms=spec['keyterms'], context=spec['context'])
            transcript = response.get('transcript')
            if not isinstance(transcript, str):
                raise RuntimeError('Prisma response missing transcript; resume from cache after investigating')
            llm_hits += int(extract.cached_available(spec['question'], transcript, question_key=spec['question_key'], allow_same_day=spec['question'] == 'P3'))
            details = {}
            # Transport/rate errors propagate: never turn them into invalid_llm_output.
            result = extract.extract(spec['question'], transcript, question_key=spec['question_key'],
                allow_real=True, details=details, allow_same_day=spec['question'] == 'P3')
            errors = details.get('validation_errors', [])
            flags = redflags.detect(transcript, result, question=spec['question'], validation_errors=errors) if spec['question'] in {'P2', 'P4', 'F'} else dict(alert=False, status='not_screened', keyword_flags=[], llm_flags=[])
            clips.append(dict(**spec, file=relative, transcript=transcript, extracted=result,
                validation_errors=errors, invalid_llm_output=bool(errors), raw_llm_response=details.get('raw_response'),
                red_flags=flags, processed_at=datetime.now(timezone.utc).isoformat()))
            save_state('running')
            if len(clips) % 10 == 0 or len(clips) == len(paths):
                print('PROGRESS ' + dumps(progress()), flush=True)
    except llm.DailyQuotaError as exc:
        reset_utc = datetime.fromtimestamp(exc.reset_at, timezone.utc) if exc.reset_at is not None else None
        stop = {'reason': str(exc), 'quota': exc.quota,
                'pending_clip': current_spec, 'last_completed_clip': clips[-1]['file'] if clips else None,
                'quota_reset_utc': reset_utc.isoformat() if reset_utc else None,
                'quota_reset_ist': reset_utc.astimezone(ZoneInfo('Asia/Kolkata')).isoformat() if reset_utc else None,
                'reset_source': 'Groq retry-after/reset headers or error retry hint; unknown if absent',
                'resume_command': '.venv/bin/python eval/run_setB.py --real',
                'pending_prisma_response_cached': True}
        save_state('daily_quota_stopped', stop)
        print('DAILY QUOTA STOP — progress saved; no invalid_llm_output recorded.', flush=True)
        print(dumps({**progress(), **stop}), flush=True)
        print('Quota reset: ' + (stop['quota_reset_ist'] or 'not reported by Groq; consult the Console limits page'), flush=True)
        print('Re-run the resume command after reset. Completed clips are skipped; the pending Prisma response is cached.', flush=True)
        return None
    finally:
        if old_mock is None:
            os.environ.pop('GNANI_MOCK', None)
        else:
            os.environ['GNANI_MOCK'] = old_mock
        gnani._REAL_SCRIPT = old_real
        print(dumps({'prisma_http_attempts': gnani.STATS['real_calls'] - before_stt,
                     'groq_http_attempts': llm.STATS['real_calls'] - before_llm, 'llm_cache_hits': llm_hits}))
    sessions = []
    for (speaker, session), target in truth.items():
        group = [c for c in clips if c['speaker'] == speaker and c['session'] == session]
        record = assemble(group)
        sessions.append(dict(speaker=speaker, session=session, record=record, truth=target,
                             scores=score_session(record, target)))
    summaries = summary_rows(sessions, clips)
    session_map = {(s['speaker'], s['session']): s for s in sessions}
    clip_csv = []
    for clip in clips:
        row = {k: dumps(v) if isinstance(v, (dict, list)) else v for k, v in clip.items()}
        session = session_map[(clip['speaker'], clip['session'])]
        row['session_scores_json'] = dumps(session['scores'])
        clip_csv.append(row)
    session_csv = [dict(speaker=s['speaker'], session=s['session'], record_json=dumps(s['record']),
                        truth_json=dumps(s['truth']), scores_json=dumps(s['scores']),
                        complete_truth=s['scores']['complete_truth'], complete_record_correct=s['scores']['complete_record_correct']) for s in sessions]
    write_csv(targets[0], clip_csv)
    write_csv(targets[1], session_csv)
    write_csv(targets[2], summaries)
    save_state('complete')
    for s in summaries:
        accuracy = f'{s["accuracy"]:.1%}' if s['accuracy'] != '' else 'n.a.'
        print(f'{s["speaker"]:7} {s["field"]:40} {s["correct"]}/{s["total"]} ({accuracy})')
    print_failures(sessions, clips)
    return clips, sessions, summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real', action='store_true', help='Requires typed approval of displayed budget')
    args = parser.parse_args()
    paths, truth, prompts, medicines, symptoms = load_inputs()
    verify_protocol(paths)
    plan = call_plan(paths, prompts, medicines, symptoms)
    destination = ROOT / 'eval/setB_full_v1_call_plan.json'
    destination.write_text(json.dumps(plan, indent=2) + '\n')
    if not args.real:
        print('STOP: confirm this call-count gate before --real. No real evaluation calls made.')
        return
    if input('Type RUN FULL SET B to authorize the displayed calls: ') != 'RUN FULL SET B':
        raise SystemExit('Cancelled')
    run(paths, truth, prompts, medicines, symptoms, allow_real=True)


if __name__ == '__main__':
    main()
