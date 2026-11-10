#!/usr/bin/env python3
"""Eight invented examples with simulated provider output; never makes API calls."""
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import extract
import redflags


def item(value, evidence='', status='ok'):
    return {'value': value, 'status': status, 'evidence': evidence}


# Author-written responses test plumbing/validation, not live LLM accuracy.
EXAMPLES = [
    ('P0', 'Mera token satrah hai.', None, {'token': item(17, 'satrah')}),
    ('F', 'Haan, thermometer se naapa tha.', 'measured',
     {'follow_up': item({'question_key': 'measured', 'value': True}, 'Haan, thermometer se naapa tha.'),
      'red_flag_symptoms': item([], 'Haan, thermometer se naapa tha.')}),
    ('F', 'Dard aath hai aur saans nahi aa rahi.', 'pain_score',
     {'follow_up': item({'question_key': 'pain_score', 'value': 8}, 'Dard aath hai'),
      'red_flag_symptoms': item(['breathlessness'], 'saans nahi aa rahi')}),
    ('R1', 'Haan, aapne dawai sahi boli.', None,
     {'confirmed': item(True, 'Haan, aapne dawai sahi boli.'), 'correction': item(None, status='unclear')}),
    ('R1', 'Nahi, dose bees milligram hai.', None,
     {'confirmed': item(False, 'Nahi'), 'correction': item('dose bees milligram hai', 'dose bees milligram hai')}),
    ('P6', 'Mujhe kisi dawai se allergy nahi hai.', None,
     {'allergies': item('none', 'kisi dawai se allergy nahi hai')}),
    ('P6', 'Mujhe nahi pata kis dawai se allergy hai.', None,
     {'allergies': item('unknown', 'Mujhe nahi pata kis dawai se allergy hai.')}),
    ('P7', 'Mujhe sugar aur asthma hai.', None,
     {'conditions': item(['diabetes', 'asthma'], 'sugar aur asthma')}),
]


def main():
    rows = []
    with tempfile.TemporaryDirectory() as folder, patch.object(extract, 'ROOT', Path(folder)), \
         patch('llm.settings', return_value=('offline', 'simulated-stage2')), \
         patch('requests.request', side_effect=AssertionError('Network forbidden')):
        for question, transcript, key, fixture in EXAMPLES:
            details = {}
            raw = {'choices': [{'message': {'content': json.dumps(fixture)}}]}
            with patch('llm.complete_json', return_value=(fixture, raw)):
                result = extract.extract(question, transcript, question_key=key, details=details)
            assert result == fixture and not details['validation_errors']
            flags = redflags.detect(transcript, result, question=question)
            row = dict(question=question, question_key=key, transcript=transcript,
                       extracted=result, red_flags=flags, provider='simulated_offline_fixture')
            rows.append(row)
            print(json.dumps(row, ensure_ascii=False))
    destination = Path(__file__).resolve().parents[1] / 'archive/examples/setB_stage2_outputs.json'
    destination.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
