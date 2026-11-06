# Full Set B evaluation

Use the project venv from the repository root:

```bash
.venv/bin/python eval/run_setB.py
```

This only checks files, the frozen protocol, cache availability and the API/time budget. It makes no network calls. The full protocol and scoring limitations are in [SETB_SCORING_NOTES.md](SETB_SCORING_NOTES.md).

Only after explicit approval of that budget:

```bash
.venv/bin/python eval/run_setB.py --real
```

Type `RUN FULL SET B` when prompted. This processes all 212 copied M4As (106 per speaker), including follow-ups, R1 and P0/P6/P7. It uses cached responses where parameters match and resumes transport failures from cache/checkpoint. Groq calls pace to observed headers and allow five retries. A 429 is never a validation failure.

First full-run outputs are `eval/results/setB_per_clip.csv`, `setB_per_session.csv`, and `setB_summary.csv`; they are protected from overwrite. The earlier exploratory results remain intact, and the earlier runner is preserved as `eval/run_setB_legacy.py`. Avoid using that old runner for the full evaluation.

Ground truth now covers 20/20 sessions. User-supplied S02 facts accept back of head OR near neck, and pain score 5. Progress prints every 10 clips. Daily quota exhaustion saves progress and exits cleanly, showing the pending clip and server-reported reset time. Re-run the same command after reset; completed clips are skipped and the pending Prisma response is reused from cache.

Rate headers confirm RPD and TPM; they may not report RPM/TPD. The preflight time is a conservative pacing estimate, excluding Prisma time, response latency, external organization traffic and daily quota resets. Exact account quotas not returned by the API must be read from the Groq Console limits page.

## Official v1 completion and resume

All 212 clips are now complete. See [the frozen report](results/SETB_V1_REPORT.md) and [resume operations](SETB_RESUME_OPERATIONS.md). The final operational runner is `eval/resume_setB_v1.py`; it preserves the original model/medium reasoning and stops cleanly only on an actual daily-limit HTTP 429. Minute limits retry with backoff. Completed v1 outputs cannot be overwritten; do not start a new experiment in those files.
