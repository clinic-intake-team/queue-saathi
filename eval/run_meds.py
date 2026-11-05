#!/usr/bin/env python3
"""Frozen Set A raw-STT evaluation. Default is a network-free plan, not a run."""
import argparse
import csv
import json
import os
from pathlib import Path
import re
import sys
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gnani

ROOT = gnani.ROOT
# Fixed before looking at evaluation output. These are transliterations, not fuzzy matches.
DEVANAGARI_BRANDS = {
    'टेल्मा': 'telma', 'टेलमा': 'telma', 'डोलो': 'dolo',
    'ग्लाइकोमेट': 'glycomet', 'ग्लाइकोमैट': 'glycomet', 'ग्लायकोमेट': 'glycomet',
    'थायरोनॉर्म': 'thyronorm', 'थायरोनार्म': 'thyronorm', 'थाइरोनॉर्म': 'thyronorm',
    'पैन': 'pan', 'इकोस्प्रिन': 'ecosprin', 'इकोस्प्रीन': 'ecosprin', 'एकोस्प्रिन': 'ecosprin',
    'एमलॉन्ग': 'amlong', 'एमलोंग': 'amlong', 'अमलॉन्ग': 'amlong',
    'मेटफॉर्मिन': 'metformin', 'मेटफोरमिन': 'metformin',
    'एटोरवास्टेटिन': 'atorvastatin', 'अटोरवास्टेटिन': 'atorvastatin',
    'मोंटेयर': 'montair', 'मॉन्टेयर': 'montair', 'मोंटेर': 'montair',
    'एलसी': 'lc', 'एल सी': 'lc', 'अस्थालिन': 'asthalin', 'एस्थालिन': 'asthalin',
    'शेलकैल': 'shelcal', 'शेलकाल': 'shelcal', 'शेलकल': 'shelcal',
    'अपराइज': 'uprise', 'अपराइज़': 'uprise', 'अप राइज': 'uprise',
    'डी': 'd', 'जानुमेट': 'janumet', 'जैनुमेट': 'janumet',
    'पैंटोसिड': 'pantocid', 'पेन्टोसिड': 'pantocid', 'पेंटोसिड': 'pantocid',
    'कॉम्बिफ्लेम': 'combiflam', 'कॉम्बिफ्लैम': 'combiflam', 'कंबिफ्लेम': 'combiflam',
    'अजिथ्राल': 'azithral', 'एज़िथ्राल': 'azithral', 'अज़िथ्राल': 'azithral',
    'क्रोसिन': 'crocin', 'सेटज़िन': 'cetzine', 'सेटजिन': 'cetzine', 'सेट्जिन': 'cetzine',
    'रोसुवास': 'rosuvas', 'रोजुवास': 'rosuvas', 'क्लोपिलेट': 'clopilet',
    'बुडेकोर्ट': 'budecort', 'ब्यूडेकोर्ट': 'budecort',
    'डेरीफिलिन': 'deriphyllin', 'डेरिफिलिन': 'deriphyllin',
    'लैंटस': 'lantus', 'लांटस': 'lantus',
}
NUMBER_GROUPS = {
    0: 'zero शून्य', 1: 'one ek एक', 2: 'two do दो', 3: 'three teen तीन',
    4: 'four chaar char चार', 5: 'five paanch panch पांच पाँच',
    6: 'six chhe che chhah छह छः छे', 7: 'seven saat सात',
    8: 'eight aath आठ', 9: 'nine nau नौ', 10: 'ten das दस',
    11: 'eleven gyarah ग्यारह', 12: 'twelve barah बारह',
    20: 'twenty bees बीस', 25: 'pachchees pachchis pachchees pachis पच्चीस',
    30: 'thirty tees तीस', 40: 'forty chaalis chalis चालीस',
    50: 'fifty pachaas pachas पचास', 60: 'sixty saath साठ',
    70: 'seventy sattar सत्तर', 75: 'pachhattar pachattar पचहत्तर',
    80: 'eighty assi अस्सी', 90: 'ninety nabbe नब्बे',
}
NUMBERS = {word: value for value, words in NUMBER_GROUPS.items() for word in words.split()}


def normalize(text):
    text = unicodedata.normalize('NFC', text).lower()
    text = ''.join(str(unicodedata.digit(c)) if c.isdecimal() else c for c in text)
    text = ''.join(' ' if unicodedata.category(c)[0] in ('P', 'S') else c for c in text)
    for source, target in sorted(DEVANAGARI_BRANDS.items(), key=lambda item: -len(item[0])):
        text = re.sub(r'(?<!\w)' + re.escape(source) + r'(?!\w)', target, text)
    tokens = text.split()
    result = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        value = NUMBERS.get(token)
        if value is None:
            result.append(token)
            index += 1
            continue
        index += 1
        if index < len(tokens) and tokens[index] in ('hundred', 'sau', 'सौ'):
            value *= 100
            index += 1
            if index < len(tokens) and tokens[index] == 'and':
                index += 1
            if index < len(tokens) and tokens[index] in NUMBERS:
                value += NUMBERS[tokens[index]]
                index += 1
        elif value in (20, 30, 40, 50, 60, 70, 80, 90) and index < len(tokens) and 0 < NUMBERS.get(tokens[index], 0) < 10:
            value += NUMBERS[tokens[index]]
            index += 1
        result.append(str(value))
    return ' '.join(result)


def score(transcript, medicine):
    normalized = normalize(transcript)
    name = normalize(medicine['name']).replace(' ', '')
    # Allow inserted spaces within a brand, but require boundaries around the name.
    pattern = r'(?<!\w)' + r'\s*'.join(re.escape(c) for c in name) + r'(?!\w)'
    found = bool(re.search(pattern, normalized))
    strength = str(medicine['strength'])
    correct = found and bool(re.search(r'(?<!\d)' + re.escape(strength) + r'(?!\d)', normalized)) if strength else ''
    return found, correct


def inputs():
    with (ROOT / 'data/setA_ground_truth.csv').open(encoding='utf-8', newline='') as f:
        truth = {row['clip_id']: json.loads(row['medicines']) for row in csv.DictReader(f)}
    assert set(truth) == {f'M{i:02}' for i in range(1, 21)}, 'Invalid ground truth IDs'
    terms = [line.strip() for line in (ROOT / 'data/medicines.txt').read_text().splitlines() if line.strip()]
    if not 1 <= len(terms) <= 200:
        raise ValueError('Medicine list must contain 1–200 terms')
    paths = sorted((ROOT / 'recordings').glob('*_M??.*'))
    ids = []
    for path in paths:
        match = re.fullmatch(r'(ch|tm)_(M\d{2})\.(m4a|wav|mp3|ogg|flac|aac)', path.name)
        if not match:
            raise ValueError(f'Unexpected evaluation file: {path.name}')
        ids.append((match[1], match[2]))
    expected = {(speaker, f'M{i:02}') for speaker in ('ch', 'tm') for i in range(1,21)}
    if len(ids) != 40 or set(ids) != expected:
        raise ValueError('Expected exactly one recording for each speaker and M01–M20')
    return paths, truth, terms


def plan(paths, terms):
    seen = set()
    hits = 0
    misses = 0
    for path in paths:
        for keyterms in (None, terms):
            cache = gnani.stt_cache_path(path, keyterms, mock=False)
            if cache.exists():
                value = json.loads(cache.read_text())
                if not isinstance(value.get('transcript'), str):
                    raise ValueError(f'Invalid cached transcript: {cache.name}')
                hits += 1
            elif cache in seen:
                hits += 1
            else:
                misses += 1
            seen.add(cache)
    print(f'Plan: {len(paths)} recordings × 2 conditions = {len(paths)*2} STT requests')
    print(f'Real API calls planned: {misses}; cache hits: {hits}')
    print(f'Up to {misses*3} HTTP attempts if retries are needed (3 attempts maximum per call).')
    return misses, hits


def write_csv(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def run(paths, truth, terms):
    rows = []
    gnani.STATS.update(real_calls=0, cache_hits=0)
    try:
        for path in paths:
            speaker, clip = path.stem.split('_')
            for condition, keyterms in [('keyterms_off', None), ('keyterms_on', terms)]:
                response = gnani.stt(path, keyterms=keyterms)
                transcript = response['transcript']
                if not isinstance(transcript, str):
                    raise ValueError('Prisma transcript must be a string')
                for medicine in truth[clip]:
                    included = medicine['name'] not in ('name_unknown', 'none')
                    name_ok, strength_ok = score(transcript, medicine) if included else ('', '')
                    rows.append(dict(speaker=speaker, clip=clip, condition=condition,
                                     transcript=transcript, medicine=medicine['name'],
                                     strength=medicine['strength'], scored=int(included),
                                     name_correct=int(name_ok) if included else '',
                                     strength_correct=int(strength_ok) if included and strength_ok != '' else ''))
    finally:
        print(f"Actual real API calls (including retries): {gnani.STATS['real_calls']}; cache hits: {gnani.STATS['cache_hits']}")
    summary = []
    for speaker in ('overall', 'ch', 'tm'):
        for condition in ('keyterms_off', 'keyterms_on'):
            group = [r for r in rows if r['scored'] and r['condition']==condition and (speaker=='overall' or r['speaker']==speaker)]
            strengths = [r for r in group if r['strength'] != '']
            names_correct = sum(r['name_correct'] for r in group)
            both_correct = sum(r['strength_correct'] for r in strengths)
            summary.append(dict(speaker=speaker, condition=condition,
                                names_correct=names_correct, names_total=len(group),
                                name_accuracy=names_correct/len(group) if group else '',
                                name_strength_correct=both_correct, name_strength_total=len(strengths),
                                name_strength_accuracy=both_correct/len(strengths) if strengths else ''))
    output = ROOT / 'eval/results'
    write_csv(output/'setA_per_clip.csv', rows, list(rows[0]))
    write_csv(output/'setA_summary.csv', summary, list(summary[0]))
    print('\nSpeaker  Condition       Name accuracy     Name+strength (strength-bearing medicines only)')
    for s in summary:
        print(f"{s['speaker']:8} {s['condition']:15} {s['names_correct']}/{s['names_total']} ({s['name_accuracy']:.1%})    {s['name_strength_correct']}/{s['name_strength_total']} ({s['name_strength_accuracy']:.1%})")
    print('\nFAILED clips — ch only:')
    for r in rows:
        if r['speaker']=='ch' and r['scored'] and (not r['name_correct'] or r['strength_correct']==0):
            print(f"{r['clip']} | {r['condition']} | expected: {r['medicine']} {r['strength']} | {r['transcript']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real', action='store_true', help='Request a real run, with interactive confirmation')
    args = parser.parse_args()
    paths, truth, terms = inputs()
    plan(paths, terms)
    if not args.real:
        print('DRY PLAN ONLY: no API calls or result files. Run with --real only after approval.')
        return
    if input('Type RUN SET A to confirm real API calls: ') != 'RUN SET A':
        raise SystemExit('Cancelled; no API calls made.')
    os.environ['GNANI_MOCK'] = '0'
    gnani._REAL_SCRIPT = True
    run(paths, truth, terms)


if __name__ == '__main__':
    main()
