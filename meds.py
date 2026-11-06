"""Local medicine matching. No network; vocabulary is data/medicines.txt."""
from pathlib import Path
import re

from rapidfuzz.fuzz import ratio
from eval.run_meds import normalize

ROOT = Path(__file__).resolve().parent
THRESHOLD = 85


def vocabulary():
    # A strength in the keyterm list is not evidence that a patient said it.
    terms = []
    for line in (ROOT / 'data/medicines.txt').read_text().splitlines():
        name = re.sub(r'\s+\d+(?:\.\d+)?$', '', line.strip())
        if name and name not in terms:
            terms.append(name)
    return terms


def parse(transcript, *, fuzzy=True):
    """Return transcript-supported names/strengths and purpose-only unknowns.

    Greedy non-overlapping phrase matching, ratio >=85, exact-only if fuzzy=False.
    Strength belongs to the immediately following numeric phrase, never another medicine.
    Matching alone needs confirmation; only an explicit R1 can confirm it later.
    """
    text = normalize(transcript)
    tokens = text.split()
    candidates = []
    for name in vocabulary():
        canonical = normalize(name).replace(' ', '')
        size = len(normalize(name).split())
        for start in range(len(tokens)):
            for length in range(1, max(size + 2, 3)):
                end = start + length
                if end > len(tokens):
                    continue
                phrase = tokens[start:end]
                if any(t.isdecimal() for t in phrase):
                    continue
                score = ratio(''.join(phrase), canonical)
                if score >= (THRESHOLD if fuzzy else 100):
                    candidates.append((score, len(canonical), start, end, name))
    used = set()
    selected = []
    denied_names = set()
    for score, _, start, end, name in sorted(candidates, key=lambda c: (-c[0], -c[1], c[2], c[4])):
        positions = set(range(start, end))
        if not positions & used:
            # Do not collect a medicine explicitly denied or superseded by a correction.
            before = tokens[max(0, start - 2):start]
            after = tokens[end:end + 2]
            negated = (any(t in {'no', 'not'} for t in before)
                       or bool(after and after[0] in {'nahi', 'nahin', 'नहीं'}))
            if negated:
                denied_names.add(name)
            if not negated:
                selected.append((start, end, name, score))
                used |= positions
    selected.sort()
    medicines = []
    for start, end, name, score in selected:
        if name in denied_names:
            continue
        strength = None
        if end < len(tokens) and re.fullmatch(r'\d+(?:\.\d+)?', tokens[end]):
            strength = tokens[end]
        medicines.append({'name': name, 'strength': strength, 'purpose': None,
                          'display': name + (' ' + strength if strength else ''),
                          'match_score': round(score, 2), 'status': 'needs_confirmation'})
    # Explicit ignorance OR purpose-only naming supports an unknown-name entry.
    purposes = {'BP': r'\bbp\b|blood pressure|ब्लड प्रेशर|बीपी',
                'sugar': r'\bsugar\b|\bdiabet\w*|शुगर|मधुमेह',
                'thyroid': r'\bthyroid\b|थायरॉइड|थायराइड'}
    ignorance = r'yaad nahi|naam nahi|nam nahi|don.t (?:know|remember)|name unknown|नाम.*(?:याद नहीं|नहीं पता)'
    purpose_matches = [p for p, pattern in purposes.items() if re.search(pattern, text)]
    # Explicit unknown-name references can follow a sentence break or contrast.
    segments = [text] if len(purpose_matches) == 1 else re.split(r'[.;।]|\b(?:aur|and|but|lekin)\b', text)
    for segment in segments:
        for purpose, pattern in purposes.items():
            if not re.search(pattern, segment):
                continue
            explicit_unknown = re.search(ignorance, segment)
            purpose_only = re.search(r'(?:ki|ke|ka)\s+(?:goli|dawai|dawa)|medicine|tablet|(?:की|के लिए).*?(?:गोली|गोलियाँ|दवा)', segment)
            named_in_segment = any(normalize(m['name']).replace(' ', '') in segment.replace(' ', '') for m in medicines)
            if explicit_unknown or (purpose_only and not named_in_segment):
                display = purpose + ' medicine (name unknown)'
                if not any(m['display'] == display for m in medicines):
                    medicines.append({'name': None, 'strength': None, 'purpose': purpose,
                                      'display': display, 'match_score': None,
                                      'status': 'unknown_name_with_purpose'})
    return medicines


def readback(medicines):
    if not medicines:
        return 'Kya aap koi dawai nahi le rahe hain?'
    return 'Aapne bataya: ' + ', '.join(m['display'] for m in medicines) + '. Kya yeh sahi hai?'


def apply_confirmation(medicines, transcript, extracted):
    """Only accept a validated explicit R1 agreement; corrections need new read-back."""
    import extract
    checked = extract.validate('R1', transcript, extracted)
    accepted = (checked['confirmed']['status'] == 'ok'
                and checked['confirmed']['value'] is True
                and checked['correction']['status'] != 'ok')
    return [dict(m, status='confirmed' if accepted else m['status']) for m in medicines]
