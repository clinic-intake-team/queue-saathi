#!/usr/bin/env python3
"""Render fixed prompts offline by default. Real: GNANI_MOCK=0 python scripts/generate_prompts.py --real"""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml
import gnani


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real', action='store_true')
    args = parser.parse_args()
    gnani._REAL_SCRIPT = args.real
    mode = 'mock (silent placeholders)' if gnani._mock() else 'REAL (uses credits)'
    print(f'Generating prompts: {mode}')
    prompts = yaml.safe_load((gnani.ROOT / 'prompts.yaml').read_text(encoding='utf-8'))
    for prompt_id, text in prompts.items():
        output = gnani.tts(text, gnani.ROOT / 'assets/prompts' / f'{prompt_id}.wav')
        print(output)


if __name__ == '__main__':
    main()
