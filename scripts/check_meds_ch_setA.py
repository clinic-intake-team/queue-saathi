#!/usr/bin/env python3
"""Offline medicine development report: only ch Set A cached STT, no API fallback."""
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gnani
import meds


def main():
    terms = [s.strip() for s in (gnani.ROOT / 'data/medicines.txt').read_text().splitlines() if s.strip()]
    rows = []
    with patch('requests.request', side_effect=AssertionError('No API calls allowed')):
        # Never glob other speakers, Set B files, or arbitrary cache contents.
        for audio in sorted((gnani.ROOT / 'recordings').glob('ch_M??.m4a')):
            for condition, keyterms in [('keyterms_off', None), ('keyterms_on', terms)]:
                path = gnani.stt_cache_path(audio, keyterms, mock=False)
                if not path.exists():
                    raise RuntimeError('Required cached ch Set A response missing: ' + audio.name)
                transcript = json.loads(path.read_text())['transcript']
                rows.append(dict(clip=audio.stem, condition=condition, transcript=transcript,
                                 medicines=meds.parse(transcript)))
    destination = gnani.ROOT / 'examples/meds_ch_setA_development.json'
    destination.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    print(f'Reviewed {len(rows)} cached ch Set A transcripts only; no API calls.')
    print('Saved ' + str(destination))


if __name__ == '__main__':
    main()
