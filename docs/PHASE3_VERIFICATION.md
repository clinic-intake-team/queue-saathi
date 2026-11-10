# QueueSaathi — Phase 3 mock patient flow

## Implemented

- Brighter blue hero arc; higher-contrast small labels; fictional doctor-summary
  product preview below the landing statistics, including a red-flag banner,
  medicines with an unclear chip and an illustrative evidence quote.
- Patient questions, silent cached mock prompt playback/replay, browser microphone
  recording using MediaRecorder, live analyser waveform, 45-second cap, and upload
  through the existing ffmpeg converter.
- Sample-answer alternative when microphone permission is denied or unavailable.
- “Maine suna” review, gentle re-ask, medicine read-back with explicit confirmation
  or correction, red/amber alert interruptions, done token and local session restore.
- “Record again / Dobara record karein” on transcript review restores the same
  question, removes the old answer from active fields, and preserves the previous
  clip separately in superseded_answers. Repeated recording replaces the answer.
  The final answer is reviewed before completion too. Alerts cannot be erased.
- Existing extraction prompts, validation rules, clinical red-flag/medicine modules
  and evaluation code remain unchanged. Real UI API calls remain blocked.

## Checks

- 76 Python tests pass, including conversion, explicit medicine correction and
  confirmation, stale submissions, re-asks, alert interruptions, redo of initial
  and final answers, legacy-session redo, and alert protection.
- Production TypeScript/Vite build passes.
- Screenshot-free Playwright checks passed before the final redo addition:
  responsive 320/390/1440 layouts; no axe color-contrast/name/ARIA violations on
  landing plus eight sample screens; full mock flow; real MediaRecorder WebM
  upload using a fake browser microphone; denied-microphone fallback; correction,
  red/amber alerts, re-ask and session restore. No browser runtime errors or paid
  API requests.
- Final browser re-check after adding redo was declined. The redo backend tests
  and updated frontend production build passed. No screenshots were taken.

## Open locally

`PORT=8018 make dev` starts backend + frontend with GNANI_MOCK=1.

- Full interactive flow: http://127.0.0.1:5173/intake?new=1
- Question: http://127.0.0.1:5173/intake?screen=question
- Simulated recording: http://127.0.0.1:5173/intake?screen=recording
- Transcript review: http://127.0.0.1:5173/intake?screen=transcript
- Medicine read-back: http://127.0.0.1:5173/intake?screen=readback
- Red flag: http://127.0.0.1:5173/intake?screen=red-flag
- Needs check: http://127.0.0.1:5173/intake?screen=needs-check
- Done: http://127.0.0.1:5173/intake?screen=done
- Re-ask: http://127.0.0.1:5173/intake?screen=unclear

Screen URLs are fictional showcases, not live sessions, and never automatically
request microphone access. Full-flow recordings use fixed, labelled sample
transcripts in mock mode. Mock question audio is silent; real Timbre/Groq/Prisma
sessions require the user's separate confirmation before enabling them.

The current checkout has no original flow.py. This phase wraps the existing
standard P0–P7 sequence plus R1; adaptive follow-up orchestration is not added.
