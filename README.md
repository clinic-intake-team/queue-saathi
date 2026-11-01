# Clinic Queue Intake

Phase 1 skeleton in the existing project root. Python, Streamlit, Prisma v3.0 STT and Timbre v3.0 TTS. Intake logic and extraction are later phases.

```sh
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

## Offline use

`GNANI_MOCK` defaults to `1` even when absent from `.env`. Set `GNANI_MOCK=1` in `.env` for normal development. Imports never call the API.

```sh
python gnani.py test.wav
python gnani.py test.wav --keyterms Telma 'Telma 40' Glycomet
python scripts/generate_prompts.py
```

STT fixtures reproduce the two transcripts recorded in `credits.md`. Full Step 0 response JSON was not saved, so fixtures contain only the observed transcript, without invented request IDs or timing. These are canned responses for any input in mock mode, not transcription. Number forms are preserved verbatim: `2` and `दो` must both be supported by future extraction.

Mock TTS generates one second of silent WAV audio with a `.wav.mock` sidecar. These placeholders are replaced when explicitly generating real prompts; existing real audio is reused. Mock and real STT cache keys are separate.

## Explicit real calls

Only run these when you intend to spend credits. Both `GNANI_MOCK=0` and `--real` are required for the Phase 1 scripts:

```sh
GNANI_MOCK=0 python gnani.py --real test.wav
GNANI_MOCK=0 python scripts/generate_prompts.py --real
```

The client retries HTTP 429/500/503 with exponential backoff, up to three total attempts. It does not retry transport errors or follow redirects. Every actual attempt is logged in `logs/api_calls.csv`. STT is cached by audio bytes and request parameters; TTS skips existing real output. Fixed prompts include follow-ups and exclude the dynamic medicine read-back.

The separate `scripts/step0_credit_test.py` remains an explicitly interactive real-call credit test with exactly three attempts and no retries. Do not rerun it for UI development.

Put `GNANI_API_KEY` in `.env`. `.env` is ignored, but it was already Git-tracked before Phase 1; ignoring does not remove tracking. Never commit a populated `.env`.
