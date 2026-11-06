# Set B test run guide

Set B is the 10 full-session cases `S01`–`S10`. The current `raw/setB_tm/` folder contains 106 teammate recordings: 80 standard questions (`P0`–`P7`) and 26 follow-ups/read-backs. Counts vary by session (9–12 files). The evaluator reads these files in place and does not rename or alter them.

## What this run measures

`eval/run_setB.py` replays each recording as a separate Prisma STT request, with its question as context and medicine/symptom keyterms for P5/P2/P4. It then runs Groq extraction for P1–P5, and computes the P4 red-flag output. P0, P6, P7 and follow-ups/R1 are transcribed and saved but have no structured extraction schema in this evaluator. This is not a live multi-turn app-flow test, and there is no phone/noise condition in this run.

The existing evaluator stores one row per recording in `eval/results/setB_per_recording.csv`. It does not currently produce a scored accuracy summary. Treat the extraction and red-flag columns as review data; compare them against the session facts in `test-scripts.md` before reporting results.

## 1. Create the two API keys

The project uses **Gnani** for speech-to-text and **Groq** for structured extraction. “Grok” is xAI's separate product; this repository is configured for Groq (`LLM_PROVIDER=groq`, `GROQ_API_KEY`).

1. Sign in to [Gnani Voice](https://app.gnani.ai/voice) with the project account. Open API keys in the dashboard and create/copy a key with STT access/credits. Gnani calls use `GNANI_API_KEY`.
2. Sign in to [GroqCloud API Keys](https://console.groq.com/keys) and create/copy a key. Groq may require a project and developer/owner role. The Set B extraction calls need model access and available quota.
3. In `Gnani_Hackathon`, create a local `.env` from `.env.example` if needed, then fill these values locally:

   ```dotenv
   GNANI_MOCK=1
   GNANI_API_KEY=your_gnani_key
   LLM_PROVIDER=groq
   LLM_MODEL=openai/gpt-oss-120b
   GROQ_API_KEY=your_groq_key
   ```

   Keep both values private. Never paste them into chat, commit them, or put them in a command line. `.env` is ignored by Git. The evaluator requires an explicit `--real` run to enable paid requests; `GNANI_MOCK=1` is okay for preflight and is switched internally only after the confirmation phrase.

## 2. Confirm the recordings and naming

Expected pattern: `B_S01_P0.m4a`, `B_S01_F01.m4a`, `B_S01_R1.m4a` through session `S10`. Set B filenames are standardized in both speaker folders to zero-padded session IDs, uppercase IDs, and per-session follow-up IDs (`F01`–`F03`). The numbers are identifiers, not a claim about conversation order. `eval/setB_recording_name_map.csv` records each original filename and label; the evaluator uses it to restore the original `tm` follow-up question context. Chill's original `F1`/`F2` names did not state the question, so the map preserves them without guessing. Keep the audio and map together. The evaluator currently expects exactly 106 valid audio files in `raw/setB_tm/`, 80 standard plus 26 follow-ups/read-backs, nonempty and under 30 seconds each.

Optional read-only inventory (reports counts, duration, hashes, and proposed mapping; does not call APIs):

```powershell
python scripts/inventory_setB.py
```

Then run the evaluator preflight. From the repository root:

```powershell
python eval/run_setB.py
```

Review its counts and cache/call budget. This command makes no API calls. To inspect a small selection first, for example P1 only:

```powershell
python eval/run_setB.py --question P1
```

## 3. Run the paid evaluation

When the preflight looks right, run:

```powershell
python eval/run_setB.py --real
```

The script prints the plan again. Type exactly `RUN SET B` only when you are ready to spend the displayed Gnani and Groq budget. `--question P1` or `--limit N` can restrict a run for a small initial check; note that output is written to the same CSV, so full-run output replaces a partial run's CSV when it starts.

Successful STT and extraction responses are cached, so a later run can resume without paying again for cached work. HTTP 429/5xx responses may be retried up to three attempts. Each actual attempt is logged without the key in `logs/api_calls.csv` (Gnani) or `logs/llm_calls.csv` (Groq).

## 4. Review the output

Open `eval/results/setB_per_recording.csv`. Filter by `session` and `recording_id`; inspect transcript, `extracted_json`, `validation_errors`, and P4's `red_flag`, `keyword_flags`, and `llm_flags`. Compare with the corresponding S01–S10 facts in `test-scripts.md`. Preserve the CSV and protocol/configuration used for the run before changing prompts, schemas, keyterms, model, or scoring rules.

## Naming correction

`eval/README.md` documents Set A medicine scoring. Its heading now says Set A; use this file for Set B. `test-scripts.md` now describes the standardized Set B session IDs and recording filenames and no longer directs Set B files into the obsolete generic `.wav` naming pattern.
