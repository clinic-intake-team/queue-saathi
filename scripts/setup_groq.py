#!/usr/bin/env python3
"""Explicit setup: one model-list GET and exactly one completion POST attempt."""
import argparse
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import set_key
import llm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real', action='store_true', required=True)
    parser.parse_args()
    os.environ['LLM_PROVIDER'] = 'groq'
    set_key(str(llm.ROOT / '.env'), 'LLM_PROVIDER', 'groq')
    available = llm.list_models(allow_real=True)
    ids = sorted(item['id'] for item in available['data'] if item.get('active', True))
    print('Available models:\n' + '\n'.join(ids), flush=True)
    # Prefer documented Llama 70B+ JSON models; otherwise use available GPT-OSS 120B.
    candidates = ['llama-3.3-70b-versatile', 'llama-3.1-405b-reasoning', 'llama-3.1-70b-versatile', 'openai/gpt-oss-120b']
    model = next((name for name in candidates if name in ids), None)
    if model is None:
        raise SystemExit('No supported Llama 70B+ candidate available. No completion call made.')
    os.environ['LLM_MODEL'] = model
    set_key(str(llm.ROOT / '.env'), 'LLM_MODEL', model)
    print('Chosen model: ' + model, flush=True)
    sentence = 'Meri umar forty six saal hai.'
    parsed, raw = llm.complete_json([
        {'role':'system', 'content':'Return only a JSON object with age (integer) and evidence (exact words quoted from the input). Extract age from the user sentence.'},
        {'role':'user', 'content':sentence},
    ], allow_real=True, max_attempts=1)
    print('Test sentence: ' + sentence)
    print('Raw response:\n' + json.dumps(raw, ensure_ascii=False, indent=2))
    assert type(parsed.get('age')) is int and parsed['age'] == 46
    assert isinstance(parsed.get('evidence'), str) and parsed['evidence'] and parsed['evidence'] in sentence
    print('JSON output and age/evidence validation passed.')


if __name__ == '__main__':
    main()
