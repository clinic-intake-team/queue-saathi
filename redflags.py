"""Two-layer, negation-aware flags based on build-spec section 4.

Keyword matching is a finite heuristic, not a clinical triage system.
"""
import re
import unicodedata

PATTERNS = {
    'chest pain': r'chest\s+(?:pain|pressure|heaviness)|seene?\s+(?:mein\s+)?(?:dard|dabav)|सीने\s*(?:में\s*)?(?:दर्द|दबाव)',
    'breathlessness': r'breathless(?:ness)?|short(?:ness)?\s+of\s+breath|difficulty\s+breathing|(?:cannot|can\s*not|can.t|unable\s+to)\s+breathe|saans\s+(?:(?:nahi|nahin)\s+(?:aa\s+rahi|aati)|phool\w*|lene\s+(?:mein\s+)?(?:bahut\s+)?(?:dikkat|takleef))|सांस\s*(?:नहीं\s*आ\s*रही|फूल\w*|लेने\s*में\s*(?:बहुत\s*)?(?:दिक्कत|तकलीफ))',
    'fainting': r'faint(?:ed|ing)?|unconscious(?:ness)?|behosh\w*|बेहोश\w*',
    'seizure': r'seizures?|convulsions?|daur[ae]|jhatk[ae]|दौरा|दौरे|झटके',
    'one-sided weakness': r'one[ -]sided\s+weakness|(?:left|right)\s+(?:arm|leg|side)\s+(?:is\s+)?weak|ek\s+taraf\s+kamzori|एक\s*तरफ\s*कमजोरी',
    'facial droop': r'facial\s+droop|muh\s+tedha|मुंह\s*टेढ़ा|मुँह\s*टेढ़ा',
    'difficulty speaking': r'difficulty\s+(?:speaking|with\s+speech)|slurred\s+speech|bolne\s+(?:mein\s+)?dikkat|बोलने\s*में\s*दिक्कत',
    'vomiting blood': r'vomit(?:ing|ed)?\s+blood|blood\s+in\s+(?:the\s+)?vomit|khoon\s+ki\s+ulti|ulti\s+(?:mein\s+)?khoon|खून\s*की\s*उल्टी|उल्टी\s*में\s*खून',
    'black stool': r'black\s+(?:stools?|tarry\s+stools?)|ka+la\s+ma[ln]|काला\s*मल',
    'heavy bleeding': r'heavy\s+bleeding|bleeding\s+(?:a\s+lot|heavily)|bahu?t\s+zyada\s+khoon|बहुत\s*ज्यादा\s*खून',
}
NEGATION = r'\b(?:no|not|never|denies|denied|without|nahi|nahin|nhi)\b|नहीं|नही'
BOUNDARY = r'[.!?;।]|\b(?:but|however|lekin|magar|aur|and)\b|लेकिन|मगर|और'


def _normalize(text):
    return unicodedata.normalize('NFC', text).lower().replace('’', "'")


def _present(clause, match):
    # Negation internal to "cannot breathe" / "saans nahi aa rahi" describes distress.
    # Only examine external context, keeping symptom clauses independent.
    before, after = clause[:match.start()], clause[match.end():]
    prefix = before.split()[-4:]
    suffix = ' '.join(after.split()[:5])
    # Another symptom mention between a denial and this one prevents denial leaking.
    suffix_denial = re.search(r'\b(?:nahi|nahin|nhi)\b|नहीं|नही', suffix)
    suffix_denial = suffix_denial or re.match(r'\W*(?:(?:is|was|were|has|have|did)\s+)?(?:not|never|denied)\b', suffix)
    return not (re.search(NEGATION, ' '.join(prefix)) or suffix_denial)


def keyword_flags(transcript):
    found = []
    for clause in re.split(BOUNDARY, _normalize(transcript)):
        for label, pattern in PATTERNS.items():
            if any(_present(clause, m) for m in re.finditer(pattern, clause)):
                found.append(label)
    # Composite signs may span "and/aur"; assess them inside a contrast-bounded segment.
    for clause in re.split(r'[.!?;।]|\b(?:but|however|lekin|magar)\b|लेकिन|मगर', _normalize(transcript)):
        pregnancy = r'pregnan\w*|garbhavastha|गर्भावस्था|गर्भवती'
        bleeding_pain = r'bleeding|abdominal\s+pain|khoon|pet\s+(?:mein\s+)?dard|खून|पेट\s*में\s*दर्द'
        neck = r'stiff\s+neck|gardan\s+akad\w*|गर्दन\s*अकड़\w*'
        fever = r'high\s+fever|tez\s+bukha+r|तेज\s*बुखार'
        for label, first, second in [('pregnancy with bleeding or pain', pregnancy, bleeding_pain),
                                     ('stiff neck with high fever', neck, fever)]:
            a, b = re.search(first, clause), re.search(second, clause)
            if a and b and _present(clause, a) and _present(clause, b):
                found.append(label)
    return sorted(set(found))


P4_BLOOD_PATTERN = r'\b(?:blood|bleeding|bleed|khoon)\b|खून|रक्त'


def detect(transcript, extracted=None, *, question=None, validation_errors=None):
    """P2/P4/F uncertainty alerts; session detection ORs all answer alerts."""
    import extract as extraction
    keywords = keyword_flags(transcript)
    safety_question = question if question in {'P2', 'P4', 'F'} else (
        'P4' if question is None and isinstance(extracted, dict) and 'red_flag_symptoms' in extracted else None)
    is_p4 = safety_question == 'P4'
    llm_flags = []
    needs_check = False
    if is_p4:
        for clause in re.split(BOUNDARY, _normalize(transcript)):
            if any(_present(clause, match) for match in re.finditer(P4_BLOOD_PATTERN, clause)):
                keywords.append('blood or bleeding mention')
    if safety_question:
        errors = list(validation_errors or [])
        checked = extraction.validate(safety_question, transcript, extracted, errors=errors)
        item = checked['red_flag_symptoms']
        needs_check = item['status'] != 'ok' or any(
            error.get('field') == 'red_flag_symptoms' for error in errors)
        if item['status'] == 'ok':
            llm_flags = item['value']
    keywords = sorted(set(keywords))
    alert = needs_check or bool(keywords or llm_flags)
    return {'alert': alert, 'status': 'needs_check' if needs_check else ('alert' if alert else 'clear'),
            'keyword_flags': keywords, 'llm_flags': llm_flags}


def detect_session(answers):
    """answers: iterable of {question, transcript, extracted, validation_errors?}."""
    results = [detect(a['transcript'], a.get('extracted'), question=a['question'],
                      validation_errors=a.get('validation_errors')) for a in answers]
    return {'alert': any(r['alert'] for r in results), 'answers': results}
