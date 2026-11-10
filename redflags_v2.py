"""Part A negation overrides and session-level P4 resolution; no new symptom list."""
import copy
import re
import unicodedata

import redflags as v1

CLAUSE_BOUNDARY = v1.BOUNDARY + r'|[,，،:]'


def scoped_clauses(text):
    """Keep a standalone denial attached across a comma, not across sentences."""
    pieces = re.split('(' + CLAUSE_BOUNDARY + ')', text)
    carry = ''
    comma = {',', '，', '،', ':'}
    for index in range(0, len(pieces), 2):
        clause = pieces[index]
        previous = pieces[index - 1] if index else None
        following = pieces[index + 1] if index + 1 < len(pieces) else None
        if previous not in comma:
            carry = ''
        bare_denial = bool(clause.strip()) and not re.sub(v1.NEGATION, '', clause).strip()
        if bare_denial and following in comma:
            carry = clause.strip()
            continue
        if clause.strip():
            yield (carry + ' ' + clause).strip()
            carry = ''


def normalize(text):
    # Equivalent Hindi nasal spellings, without altering transcript/evidence storage.
    return unicodedata.normalize('NFC', text).lower().replace('’', "'").replace('ँ', 'ं')


def keyword_evidence(transcript):
    text = normalize(transcript)
    present = set(v1.keyword_flags(text))
    negated = set()
    for clause in scoped_clauses(text):
        # A denial in a separate comma clause cannot erase an earlier positive.
        present.update(v1.keyword_flags(clause))
        cleaned = re.sub(v1.NEGATION, lambda m: ' ' * len(m[0]), clause)
        for label, pattern in v1.PATTERNS.items():
            originals = list(re.finditer(pattern, clause))
            for match in originals:
                if not v1._present(clause, match):
                    negated.add(label)
            for match in re.finditer(pattern, cleaned):
                # Space replacement preserves offsets. This detects internal denial,
                # e.g. negation between a symptom noun and its verb.
                denied_inside = bool(re.search(v1.NEGATION, clause[match.start():match.end()]))
                protected_distress = any(m.start() <= match.start() and m.end() >= match.end()
                                         and v1._present(clause, m) for m in originals)
                if not protected_distress and (denied_inside or not v1._present(clause, match)):
                    negated.add(label)
    return {'present': sorted(present), 'negated': sorted(negated)}


def canonical_flag(label):
    text = normalize(label)
    if text in v1.PATTERNS:
        return text
    matches = [name for name, pattern in v1.PATTERNS.items() if re.search(pattern, text)]
    return matches[0] if len(matches) == 1 else None


def apply_negation(transcript, extracted):
    result = copy.deepcopy(extracted)
    evidence = keyword_evidence(transcript)
    denied = set(evidence['negated'])
    changes = []
    item = result.get('red_flag_symptoms')
    if item and item['status'] == 'ok':
        retained = []
        for label in item['value']:
            if canonical_flag(label) in denied:
                changes.append({'field': 'red_flag_symptoms', 'removed': label})
            else:
                retained.append(label)
        item['value'] = retained
    followup = result.get('follow_up')
    if followup and followup['status'] == 'ok':
        value = followup['value']
        if value['question_key'] == 'breathless' and value['value'] is True and 'breathlessness' in denied:
            value['value'] = False
            changes.append({'field': 'follow_up', 'question_key': 'breathless', 'value': False})
    return result, evidence, changes


def detect(transcript, extracted, *, question, validation_errors=None, keyword_info=None):
    info = keyword_info if keyword_info is not None else keyword_evidence(transcript)
    keywords = list(info['present'])
    if question == 'P4':
        for clause in scoped_clauses(normalize(transcript)):
            if any(v1._present(clause, m) for m in re.finditer(v1.P4_BLOOD_PATTERN, clause)):
                keywords.append('blood or bleeding mention')
    item = extracted.get('red_flag_symptoms')
    # Legacy Set C P2 requested complaint only. Do not invent a missing safety field.
    screened = question in {'P2', 'P4', 'F'} and item is not None
    needs_check = bool(screened and (item['status'] != 'ok' or any(
        e['field'] == 'red_flag_symptoms' for e in (validation_errors or []))))
    llm_flags = item['value'] if screened and item['status'] == 'ok' else []
    positive = bool(keywords or llm_flags)
    return {'alert': needs_check or positive,
            'status': 'needs_check' if needs_check else ('alert' if positive else 'clear'),
            'keyword_flags': sorted(set(keywords)), 'llm_flags': list(llm_flags),
            'negated_keyword_flags': info['negated'], 'positive_alert': positive,
            'needs_check_cleared_by_p4': False}


def resolve_session(clips):
    """A valid P4 denial clears only P2/F uncertainty; positives always alert."""
    result = copy.deepcopy(clips)
    denial = any(c['question'] == 'P4'
        and c['extracted'].get('red_flag_symptoms', {}).get('status') == 'ok'
        and c['extracted']['red_flag_symptoms']['value'] == []
        and not c['red_flags']['positive_alert']
        and not any(e['field'] == 'red_flag_symptoms' for e in c['validation_errors'])
        for c in result)
    if denial:
        for clip in result:
            flags = clip['red_flags']
            if clip['question'] in {'P2', 'F'} and flags['status'] == 'needs_check' and not flags['positive_alert']:
                flags.update(alert=False, status='cleared_by_p4_denial', needs_check_cleared_by_p4=True)
    return result
