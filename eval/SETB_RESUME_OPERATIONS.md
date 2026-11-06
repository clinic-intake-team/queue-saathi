# Official Set B v1: operational resume

The user requested the original model and reasoning, cached Prisma, reuse of identical LLM requests, progress every 10 clips and no scores until all 212 clips are complete.

- Model remains openai/gpt-oss-120b. Reasoning is explicitly medium, equivalent to the original omitted/default effort. Medium restores the original cache key recipe; low-effort caches remain separate.
- The original extraction reference is verified against its frozen SHA-256. The resume verifier compares the AST of all extraction code except cache_path; prompt and validation must remain identical. Original scoring, ground truth, audio, keyterms and question configuration retain their hashes.
- The original official-v1 protocol/checkpoint identity stays intact. eval/setB_v1_resume_operations_response429.json fingerprints the user's latest operational changes. The earlier strict-guard fingerprint is preserved only as historical metadata.
- eval/resume_setB_v1.py prepares all missing Prisma responses before any Groq extraction. All 212 Prisma responses are now cached. Completed/cached extractions are reused before new LLM requests and whenever a matching question/context/transcript request becomes cached.
- Progress every 10 clips reports counts, elapsed time, attempts and cache/checkpoint skips. No scores are assembled, written or printed until all 212 extractions are complete.

## Response-based quota handling (latest user instruction)

There is no pre-call daily-token guard or daily-budget reservation. Missing daily headers do not block requests. Only Groq's actual HTTP 429 error body determines whether a limit is daily.

- A body mentioning tokens per day / TPD / requests per day / RPD triggers a clean exit. It saves all completed clips and preserves the pending clip's Prisma cache. The exact server message, retry hint, wait seconds and derived UTC/IST retry time are stored and printed. No daily wait is invented when the server provides none.
- Per-minute/other 429s wait and retry, respecting retry-after, with at most five retries. Normal conservative token/minute pacing remains enabled.
- Daily-limit responses are not retried in the same run. They are transport/quota events, never invalid_llm_output and never failed clips. The pending clip remains unfinished for a later resume.
- All HTTP attempts remain in logs/llm_calls.csv, including 429 status. There are no extra Prisma calls when resuming cached work.

Resume after the server's wait time:

```bash
.venv/bin/python eval/resume_setB_v1.py --real
```

A synthetic test verifies all Prisma work precedes LLM extraction, a daily 429 exits without scoring a partial run, and the next resume repeats no Prisma calls. Provider tests verify minute-limit retries, preservation of daily error messages/wait times, and that HTTP 429 cannot become a validation failure.

## Portable reference metadata after completion

The completed run used the response429 operational fingerprint retained above. For future checkouts, the exact original extraction source is committed as eval/setB_v1_extract_reference.py and its hash must match the original protocol. The resume driver now verifies that committed reference under eval/setB_v1_resume_operations_portable.json. This reference-path change does not change generation or scoring. The Set C comparison separately pins its old source Git commit in eval/setC_reasoning_reference.json, so committing newer code cannot silently replace the run-2 baseline.
