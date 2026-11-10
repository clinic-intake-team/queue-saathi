# One live intake — approved; first-use fixed cache

The user confirmed one live session and requested all fixed prompts cached once.
The live path is prepared and tested at mocked provider boundaries. Existing
Prisma/Timbre/Groq clients and approved v2 extraction/validation rules are reused.

## Expected new calls (current real TTS cache is cold)

Standard sequence: P0, P1, P2, P3, P4, P5, medicine read-back R1, P6, P7, closing P8.
This is the existing nine-answer UI sequence; it adds no adaptive follow-up calls.

| Provider | Button confirmation at R1 | Voice confirmation at R1 |
|---|---:|---:|
| Prisma v3.0 | 8 | 9 |
| Timbre v3.0 | 21 first-use / 1 warm-cache | 21 first-use / 1 warm-cache |
| Groq primary extraction | 8 | 9 |
| Possible Groq evidence-only repairs | up to 8 extra | up to 9 extra |

Timbre first-use: 20 fixed prompts (including retries, alerts and follow-ups) plus one dynamic medicine read-back. Later fixed playback is cache-only in assets/prompts/.
Voice Shivani, language hi-en. Playback reuses cached WAVs.

Groq: openai/gpt-oss-120b, medium reasoning, temperature 0, JSON-object output.
One evidence-only repair is allowed per extraction under the existing v2 policy.
Validation rejects fields that still fail. No new prompts/scoring changes.

Prisma: model prisma-v3.0, language_code hi-IN,en-IN, format transcribe;
previous_text is the current question. P2/P4 use data/symptoms.txt; P5 uses
medicine keyterms from data/medicines.txt; other questions have no keyterms.
Browser uploads are converted to 16 kHz mono PCM16 WAV before STT.

These are baseline logical calls before retries, re-asks, re-recordings,
corrections or an early red-flag stop. Cache hits reduce real calls. Each additional
voice answer can add one Prisma + one primary Groq call and possibly one evidence
repair. A new medicine read-back or re-ask audio can add Timbre. Existing clients
allow up to 3 HTTP attempts for Prisma/Timbre and up to 6 for each Groq call.
No /models listing, extra credit test, or other paid test is scheduled.

## Approved activation

After chat confirmation, restart with:

```sh
PORT=8018 .venv/bin/python scripts/dev.py --live
```

This sets GNANI_MOCK=0 in the server process, enables explicit real-client opt-in,
and reserves a single persistent UUID in ignored cache/ui_live_session_id.txt.
Repeated starts resume that same record, including after completion. Default
`make dev` stays MOCK. The local .env is not changed merely by previewing the UI.

The patient URL will be http://127.0.0.1:5173/intake?new=1. Its header shows LIVE;
sample-answer controls are hidden. Mock records retain their MOCK badges even
when viewed from a live app. The final card links to /doctor?session=<id>.

## Audit and output

- logs/ui_session_calls.csv: session UUID, provider, endpoint, model, tokens,
  HTTP status and time for every real HTTP attempt; no request bodies or keys.
- Existing logs/api_calls.csv and logs/llm_calls.csv remain active.
- GET /session/<id>/calls returns per-session counts and Groq token totals.
- data/ui_sessions/<id>.json stores the record, verbatim transcript, validated
  fields, evidence, red flags, medicine confirmation and private pipeline audit.
- Doctor view displays the record, evidence audio, transcript source badges and
  actual call totals. GET record/queue operations never synthesize speech.
- Provider errors save progress and never fall back to canned answers. Groq daily
  quota reports its reset time when supplied; retries can reuse cached Prisma.

No screenshots are required or taken. The final record remains pending the user's spoken answers.

## Superseding authorization: repeated live testing

The user subsequently authorized direct repeated Start intake actions without
per-session chat approval. The original one-session cap is removed. Explicit
`--live` mode still gates provider access; each fresh Start click creates a new
UUID and preserves existing records. No automatic provider test calls are made
when enabling this behavior. The user starts paid voice processing by recording
and submitting an answer. Fixed audio remains cache-only.
