# Set A medicine-name evaluation

Run `python eval/run_meds.py` for the default network-free plan. After approval, `python eval/run_meds.py --real` prints the plan again and requires typing `RUN SET A` before enabling real calls. No synthetic output is written to the real results directory by the offline tests.

The two conditions submit the original M4A bytes to Prisma, without conversion or context. Any future phone simulation or noise processing must first use ffmpeg to decode the source to 16-bit mono WAV; that processing is not part of this clean-audio run.

Ground truth is from `test-scripts.md`. Unknown BP medicine in M11, unknown second sugar medicine in M16, and M19's `none` are retained as unscored rows. Pantocid and Glycomet in the mixed known/unknown cards remain scored. M20 scores only Amlong.

Scoring is frozen before the first real run: lowercase, punctuation removal, fixed Devanagari transliterations, Hindi/English spoken numbers and Devanagari digits, optional spaces inside names. No fuzzy matching. Name boundaries prevent Pan from matching Pantocid or Telma from matching Telmacol. A strength is correct when the name is correct and that exact number appears anywhere in the transcript, as requested; numbers are not assigned to the nearest medicine. This raw-STT presence metric does not detect incorrect extra medicines or validate correction intent.

Name accuracy uses all known medicine mentions. Name+strength accuracy uses only mentions with an explicit ground-truth strength; strengthless entries have blank strength scores. Percentages are micro-averaged over mentions, not clips. Per-clip CSV has one row per medicine per condition, including retained unscored entries.

Real-cache planning uses the same audio-and-parameter hash as `gnani.stt`; mock caches never count. Retries on 429/all 5xx use up to three total attempts. Actual calls count all HTTP attempts; failures halt the run, preserving successful STT caches for resumption. Requests and retries are logged to `logs/api_calls.csv` without exposing the key. Only ch failures print after the run; tm results remain in CSV for the held-out evaluation.

`setA_protocol_sha256.json` records the medicine list, ground truth, scorer and API client hashes before running. Do not change the scoring rules or medicine list after viewing results unless explicitly requested.
