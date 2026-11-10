"""Predeclared Part B scoring: visit reason is separate; all old truth remains fixed."""
import copy
import re

from eval import run_setB as B
from eval import scoring_v2 as A


def complaint_correct(record, expected):
    complaint = record['complaint']
    if complaint['status'] != 'ok':
        return False
    reason = record.get('visit_reason', B.envelope())
    for concept in expected:
        value = copy.deepcopy(complaint['value'])
        if re.search(r'check|follow|review|monitor', concept, re.I) and reason['status'] == 'ok' and reason['value']:
            value['summary'] += ' ' + reason['value']
        if not A.setB_complaint(value, [concept]):
            return False
    return True


def score_setB(record, truth):
    scores = A.score_setB(record, truth)
    scores['fields']['complaint'] = B.comparison(complaint_correct(record, truth['complaint_symptoms']),
                                                record['complaint'], truth['complaint_symptoms'])
    # Additional field reporting; existing truth supplies only explicit check/follow-up purposes.
    expected = [v for v in truth['complaint_symptoms'] if re.search(r'check|follow|review|monitor', v, re.I)]
    reason = record.get('visit_reason', B.envelope())
    correct = reason['status'] == 'ok' and (
        all(A.setB_complaint({'summary': reason['value'] or '', 'symptoms': []}, [v]) for v in expected)
        if expected else reason['value'] is None)
    scores['fields']['visit_reason'] = B.comparison(correct, reason, expected or None)
    final = [v['correct'] for key, v in scores['fields'].items()
             if 'correct' in v and not key.startswith('medicines_raw') and key != 'visit_reason']
    # Complete-record definition remains comparable: reason is already required by complaint truth.
    scores['complete_record_correct'] = int(all(final)) if scores['complete_truth'] else None
    return scores
