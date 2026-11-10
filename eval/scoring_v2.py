"""Part A complaint scorer. Reuses v1 concepts; no card-specific additions."""
import copy
import re

from eval import run_setB as setB_v1
from eval import run_setC as setC_v1
import redflags_v2
import redflags


def affirmative(text, pattern):
    # Keep conjunctions inside a passage so a shared body-site can support a
    # coordinated description; explicit contrast and sentence boundaries stay local.
    for clause in redflags_v2.scoped_clauses(redflags_v2.normalize(text)):
        for match in re.finditer(pattern, clause, re.I):
            if redflags._present(clause, match):
                return True
    return False


def component_match(value, patterns):
    passages = [value['summary'], *value['symptoms']] if isinstance(value, dict) else [str(value)]
    return all(any(affirmative(passage, pattern) for passage in passages) for pattern in patterns)


def setB_complaint(value, expected):
    concepts = copy.deepcopy(setB_v1.CONCEPTS)
    # Existing anatomy/severity vocabulary, factored into independent components.
    concepts['chest heaviness'] = [r'chest|seene?|सीने', r'heav|pressure|bha+r|भारी|दबाव']
    concepts['frequent headaches'][1] += r'|\bdaily\b|\broz\b|\broj\b|रोज़?'
    return all(component_match(value, concepts[concept]) for concept in expected)


def setC_complaint(value, expected):
    return isinstance(value, dict) and all(component_match(value, setC_v1.COMPLAINT_CONCEPTS[c])
                                          for c in expected.lower().split(' + '))


def score_setB(record, truth):
    scores = setB_v1.score_session(record, truth)
    item = record['complaint']
    correct = item['status'] == 'ok' and setB_complaint(item['value'], truth['complaint_symptoms'])
    scores['fields']['complaint'] = setB_v1.comparison(correct, item, truth['complaint_symptoms'])
    final = [value['correct'] for key, value in scores['fields'].items()
             if 'correct' in value and not key.startswith('medicines_raw')]
    scores['complete_record_correct'] = int(all(final)) if scores['complete_truth'] else None
    return scores


def score_setC(truth, extracted, flags):
    scores = setC_v1.score(truth, extracted, flags)
    if truth['question'] == 'P2' and truth['expected_status'] == 'ok':
        item = extracted['complaint']
        scores['value_correct'] = int(item['status'] == 'ok' and setC_complaint(item['value'], truth['expected_value']['complaint']))
    return scores
