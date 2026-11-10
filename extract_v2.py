"""Part A normalization/validation only. No network or v1 cache writes."""
import copy
import json

import extract as v1

FIELDS = v1.FIELDS
STATUSES = v1.STATUSES
ValidationError = v1.ValidationError
ENVELOPE = {'value', 'status', 'evidence'}


def _unwrap_null(value):
    """Collapse value wrappers that contain only a null answer and metadata."""
    if isinstance(value, dict) and 'value' in value and set(value) <= {'value', 'question_key'}:
        inner = _unwrap_null(value['value'])
        if inner is None:
            return None
    return value


def validate(question, transcript, result, *, errors=None, question_key=None,
             allow_same_day=False, fields=None, normalizations=None):
    fields = tuple(fields if fields is not None else FIELDS.get(question, ()))
    if question not in FIELDS or not fields or not isinstance(transcript, str):
        raise ValidationError('Unsupported question ID, fields or transcript')
    errors = errors if errors is not None else []
    normalizations = normalizations if normalizations is not None else []
    result = copy.deepcopy(result)
    if len(fields) == 1 and isinstance(result, dict) and set(result) == ENVELOPE:
        result = {fields[0]: result}
        normalizations.append({'field': fields[0], 'change': 'restored_single_field_wrapper'})
    checked = {}
    for field in fields:
        try:
            item = result.get(field) if isinstance(result, dict) else None
            if isinstance(item, dict):
                if 'evidence' in item and item['evidence'] is None:
                    item['evidence'] = ''
                    normalizations.append({'field': field, 'change': 'null_evidence_to_empty_string'})
                if 'value' in item:
                    value = _unwrap_null(item['value'])
                    if value is None and item['value'] is not None:
                        item['value'] = None
                        normalizations.append({'field': field, 'change': 'unwrapped_nested_null'})
            if (field == 'red_flag_symptoms' and isinstance(item, dict) and set(item) == ENVELOPE
                    and item['status'] == 'ok' and item['value'] == []):
                if not isinstance(item['evidence'], str):
                    raise ValidationError('Evidence must be a string: ' + field)
                checked[field] = dict(item)
            else:
                checked[field] = v1._validate_field(field, item, transcript, allow_same_day=allow_same_day)
            if (field == 'follow_up' and checked[field]['status'] == 'ok' and question_key is not None
                    and checked[field]['value']['question_key'] != question_key):
                raise ValidationError('Follow-up key differs from the asked question')
        except (ValidationError, TypeError, ValueError) as exc:
            errors.append({'field': field, 'error': str(exc)})
            checked[field] = {'value': None, 'status': 'unclear', 'evidence': ''}
    return json.loads(json.dumps(checked, ensure_ascii=False, allow_nan=False))
