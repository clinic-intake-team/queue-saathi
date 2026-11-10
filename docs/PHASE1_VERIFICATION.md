# QueueSaathi — Phase 1 verification

## Passed

- 67 offline tests (including API credit safety, canonical audio upload, persistence,
  medicine confirmation, completed-session rejection and real-mode blocking).
- Actual curl HTTP session at localhost:8017: P0 → P1 → P2 → P3 → P4 → P5 →
  R1 → P6 → P7 → P8/ready, nine uploaded answers.
- Queue, full record, aggregate results and prompt-audio endpoints retrieved by curl.
- Synthetic session: `278ec265-ebcb-406f-bc4f-81f8a6bea61f` (local ignored data only).
- Existing extraction/red-flag/medicine logic, prompts and eval code unchanged.
- Zero cloud API calls. Mock TTS is silent and question-specific mock data is labelled.

## Previously blocked checks — now passed

- Fixed the API wrapper to prefer installed system ffmpeg without importing the
  optional `imageio_ffmpeg` fallback unnecessarily.
- Generated stereo 48 kHz WAV and Opus WebM fixtures with ffmpeg, uploaded each
  through the API test client, and verified 16 kHz mono PCM16 WAV output.
- Cloud HTTP POSTs are blocked during these tests.
- Playwright captured desktop and mobile API documentation in
  `docs/screenshots/phase1-api-desktop.png` and `phase1-api-mobile.png`.
- Full offline suite: 68 tests pass.

The original `flow.py` is absent from this checkout. The minimal mock sequence
remains deliberately limited to the Phase 1 scope; adaptive follow-ups belong to
the patient-flow phase. No existing extraction prompts, red-flag/medicine rules,
or evaluation code were changed by these UI phases.
