# Set C evaluation protocol

This document describes the version-1 run. The current development re-evaluation
uses the authorized changes and two-condition comparison in [SCORING_NOTES.md](SCORING_NOTES.md).

`python eval/run_setC.py` is a network-free preflight. It validates 24 M4A recordings (12 per speaker), ground truth, questions, keyterms, Step 1 hashes, and cache availability. It writes a protocol fingerprint, not evaluation results. No voice data is converted or changed.

After explicit approval, `python eval/run_setC.py --real` prints the call budget again and requires typing `RUN SET C`. No execution or API access occurs merely by importing the evaluator. The script enables real calls only for the confirmed run and restores the previous Prisma mock settings afterwards.

Each clip uses its ground-truth question ID. Prisma receives the original M4A, `prisma-v3.0`, `hi-IN,en-IN`, `transcribe`, and the corresponding question text as `previous_text`. Only P5 receives the 69 medicine keyterms. A real STT cache key includes audio bytes, model/language/format, keyterms, context, and real/mock mode. STT responses are never printed in preflight.

Groq extraction is cached by provider, configured model, question ID, transcript and frozen prompt. Cached results are revalidated. The initial preflight budgets 24 Prisma plus up to 24 Groq calls: Groq cache hits cannot be known until an uncached transcript is available. Identical transcripts or existing extraction cache entries may reduce that number. The per-provider HTTP attempts and cache hits are printed after the run. Retries may increase attempts; every real attempt is logged by the provider clients.

## Scoring (frozen before evaluation)

One row per clip, with 24 status and 24 value judgments. The primary field is age for P1, complaint for P2, duration_days for P3, red_flag_symptoms for P4, and medicines for P5. Missing sex is not scored against the P1 age-only ground truth.

- Status: primary field status equals expected_status.
- Non-ok value: correct status and null primary value; guessed ages/medicines do not pass.
- Age/duration: exact equality with the numeric ground truth, with status ok.
- Complaint: all expected symptom concepts and specified timing/severity modifiers must appear, using the fixed English paraphrase expressions in the scorer. Every concept must match within a summary or an individual symptom entry. Directly negated clauses do not count. This deterministic rubric uses no additional LLM judge.
- P4 extraction value: the LLM list must contain the expected positive symptom; a denial must have an empty list. This metric is separate from the combined two-layer alert.
- Red flag: only P4 is scored, comparing the combined alert to yes/no. Overall denominator is 4 positive cases and 2 negative cases; each speaker has 2 positives and 1 negative. Other questions have blank red_flag_correct.

The heuristic paraphrase scorer is an automatic proxy for semantic accuracy. It may reject correct wording outside its fixed vocabulary; it is intentionally not changed after results are seen.

## Outputs

- `eval/results/setC_per_clip.csv`: both speakers, transcripts, validated extraction JSON, layer-specific flags, combined red flag, expectations, and scores.
- `eval/results/setC_summary.csv`: overall/ch/tm accuracy fractions and percentages, positive flags caught, and false alarms.

Console progress identifies clips without disclosing transcripts. The post-run summary includes both speakers; detailed failures print for ch only. No tm failures are printed. Provider/transport failures stop execution, leaving successful caches available for resumption; no new final result CSVs are written until all 24 clips complete.

## Authorized invalid-output policy amendment

After the initial run stopped on invalid verbatim evidence, the user authorized counting rejected extractions as failed clips. Such clips use status `invalid_llm_output`, accept no extracted values (`extracted_json` is `{}`), and receive zero status/value scores. The frozen keyword layer alone decides their red flag. Validated clips keep the original scoring rules. Summaries include invalid-output counts per speaker.

Raw Groq response bodies are saved before JSON parsing or extraction validation. Rejected results are stored separately from validated caches and never retried until they pass; future runs reuse the recorded failure. The per-clip CSV includes `raw_llm_response`, `raw_response_available`, and `validation_error`. Historical responses not retained before this amendment have JSON `null` raw responses and availability zero. In particular, the previously failed extraction is recorded as invalid with its raw response explicitly unavailable, without another Groq call.

The original protocol snapshots are retained as `eval/setC_protocol_original_sha256.json` and `examples/step1_protocol_original_sha256.json`; current snapshots reflect only the authorized error-handling amendment. Extraction prompts, validation criteria, normal scoring, keyword rules, ground truth, medicine list, and recordings remain unchanged.

`examples/step1_protocol_sha256.json` locks the previously approved extraction, keyword rules and provider code. `eval/setC_protocol_sha256.json` additionally locks the scoring implementation, STT client, ground truth, question prompts, keyterms, model, and audio hashes at the call-count gate. A later mismatch stops the run rather than silently changing the protocol.
