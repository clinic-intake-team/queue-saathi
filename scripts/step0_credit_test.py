#!/usr/bin/env python3
"""Interactive credit measurement: exactly three POST attempts, no retries.

Run from any directory: python3 scripts/step0_credit_test.py
Dependencies: python3 -m pip install requests python-dotenv
Record the starting balance and balance after each call in CREDITS.md.
"""

import json
from pathlib import Path

import requests
from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://api.vachana.ai"
KEYTERMS = [
    "Telma", "Telma 40", "Glycomet", "Dolo 650",
    "Thyronorm", "Pan 40", "Ecosprin", "Amlong",
]
TEXT = (
    "Namaste! Aaj aap kis takleef ke liye aaye hain? "
    "Apne shabdon mein bataiye."
)


def report(response):
    """Print all returned JSON; successful TTS returns WAV instead of JSON."""
    print(f"HTTP status: {response.status_code}")
    try:
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    except ValueError:
        if response.content[:4] == b"RIFF" and response.content[8:12] == b"WAVE":
            print(f"Response is raw WAV audio, not JSON ({len(response.content)} bytes).")
        else:
            print("Non-JSON response:")
            print(response.text)


def main():
    key = dotenv_values(ROOT / ".env").get("GNANI_API_KEY")
    if not key or not key.strip():
        raise SystemExit("Set GNANI_API_KEY in the project root .env before running.")
    clip = next((ROOT / name for name in ("test.wav", "test.m4a")
                 if (ROOT / name).is_file()), None)
    if clip is None:
        raise SystemExit("Place test.wav or test.m4a in the project root.")
    # Read once so the two STT calls use identical bytes.
    audio = clip.read_bytes()
    if not audio:
        raise SystemExit(f"Audio file is empty: {clip.name}")
    mime = "audio/wav" if clip.suffix == ".wav" else "audio/mp4"
    headers = {"X-API-Key-ID": key.strip()}
    print(f"Using {clip.name}. This run makes three real POST attempts; no retries or redirects.")
    failures = 0
    with requests.Session() as session:
        # Explicitly prevent retrying a request that may already have spent credits.
        session.mount("https://", requests.adapters.HTTPAdapter(max_retries=0))
        for number in (1, 2, 3):
            label = {1: "STT without keyterms", 2: "STT with keyterms", 3: "TTS"}[number]
            print(f"\nCall {number}/3: {label}")
            input("Note your credit balance, then press Enter")
            try:
                if number < 3:
                    fields = {
                        "model": "prisma-v3.0",
                        "language_code": "hi-IN,en-IN",
                        "format": "transcribe",
                    }
                    if number == 2:
                        fields["keyterms"] = json.dumps(KEYTERMS)
                    response = session.post(
                        f"{BASE_URL}/stt/v3", headers=headers, data=fields,
                        files={"audio_file": (clip.name, audio, mime)},
                        timeout=(15, 120), allow_redirects=False,
                    )
                else:
                    response = session.post(
                        f"{BASE_URL}/api/v1/tts/inference", headers=headers,
                        json={
                            "text": TEXT, "model": "timbre-v3.0",
                            "voice": "Shivani", "language": "hi-en", "speed": 1.0,
                            "audio_config": {
                                "sample_rate": 16000, "num_channels": 1,
                                "sample_width": 2, "encoding": "linear_pcm",
                                "container": "wav",
                            },
                        }, timeout=(15, 120), allow_redirects=False,
                    )
            except requests.RequestException as exc:
                failures += 1
                print(f"HTTP status: unavailable ({type(exc).__name__}). No retry.")
                continue
            report(response)
            if not 200 <= response.status_code < 300:
                failures += 1
            elif number == 3:
                if response.content[:4] == b"RIFF" and response.content[8:12] == b"WAVE":
                    output = ROOT / "tts_test.wav"
                    output.write_bytes(response.content)
                    print(f"Saved {output}")
                else:
                    failures += 1
                    print("TTS did not return WAV audio; tts_test.wav was not written.")
    print("\nNote your final credit balance and record all four balances in CREDITS.md.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
