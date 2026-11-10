# Set B Stage 2 implementation and offline verification

The approved 212-file mapping was copied to recordings/ and every destination's SHA-256 verified against its source. Originals were preserved. No API calls were made.

## Extraction contract

All fields use {value, status, evidence}; statuses are ok, unclear, declined, question. Non-ok values are null. Non-null values require nonempty evidence verbatim in the transcript. Fields are independently validated; one failure preserves the other valid fields. Raw provider responses and validation diagnostics are retained in the existing versioned cache mechanism. The extended prompt separates new caches from earlier Set C caches/results.

- P0: token, nonnegative integer (boolean rejected).
- P1–P5: existing fields, plus red_flag_symptoms in P2.
- F: follow_up = {question_key, value}, plus red_flag_symptoms. Allowed question keys: temperature_f, chills, pain_location, pain_score, last_bp, last_sugar, phlegm, breathless, frequency_per_day, measured. The caller passes question_key to extract(), validate() and cached_available(); it is part of the cache key. It refers to the actual question, not an inferred session number. Bare yes/no without context must be unclear.
- R1: confirmed (boolean) and correction (nonempty text when present). An absent correction is null/unclear, not an invalid field.
- P6: allergies, nonempty list or none/unknown.
- P7: conditions, nonempty list of diabetes/BP/thyroid/asthma/other, or none.

Follow-up booleans are real JSON booleans. Numeric values must be finite and have the appropriate sign/range (pain score 0–10). BP requires both positive integer components. Unknown phlegm colour is null; denied phlegm cannot have a colour.

P2/P4/F use keyword OR validated LLM red flags. Unclear, declined, question or invalid safety fields trigger needs_check. Non-negated generic blood remains a P4-only additional rule. detect_session() ORs every answer alert so a later denial cannot clear an earlier alert.

## Medicines

meds.py uses rapidfuzz ratio >=85 against data/medicines.txt, normalized phrases and spoken strengths. fuzzy=False provides exact matching for the later evaluator. Strength is taken only from the immediately following number, not inferred from a vocabulary entry or borrowed from another medicine. Explicitly negated/corrected names are excluded. Purpose-only unknowns retain a display such as BP medicine (name unknown). Matching requests confirmation; only validated explicit R1 agreement sets confirmed. A correction requires another read-back rather than silently confirming an edited list.

Development inputs were restricted to the 40 cached STT responses for recordings/ch_M01.m4a through ch_M20.m4a (keyterms off/on). scripts/check_meds_ch_setA.py has no API fallback and never enumerates tm clips or arbitrary cache entries. See archive/examples/meds_ch_setA_development.json. This is a development inspection, not a new scored Set A result.

## Verification and limits

Run:

```bash
.venv/bin/python -m unittest discover -s tests
.venv/bin/python scripts/test_setB_stage2_examples.py
.venv/bin/python scripts/check_meds_ch_setA.py
```

The eight independently authored sentences in archive/examples/setB_stage2_outputs.json use explicitly simulated provider responses. They exercise the real extraction routing, per-field validation and red-flag code with network blocked; they do not measure live Groq accuracy. No real calls have been authorized or made at this stage.

No Set B speaking lines, script table, ground truth or audio contents were read while implementing Stage 2. No Set B evaluator or ground truth was built. Existing evaluation results were left intact. Stage 2 ends at the user's confirmation gate before Stage 3.
