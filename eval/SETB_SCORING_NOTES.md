# Full Set B v1: frozen protocol and scoring

## Scope and result provenance

This is a 212-recording full-session replay: 106 ch and 106 tm, 10 sessions each. Inputs are recordings/{speaker}_S{NN}_{row}.m4a from the approved mapping, preserving originals. Every source row, question context and duration is checked. This does not exercise the live app's adaptive question selection or interruption: even red-flag sessions process every supplied recording. No telephone/noise conversion is performed.

The earlier teammate run was exploratory: its runner is preserved as eval/run_setB_legacy.py; setB_per_recording.csv and the exploratory review files are not overwritten. The full run uses setB_per_clip.csv, setB_per_session.csv and setB_summary.csv. All first-run full v1 outputs are protected from overwrite; later changes require a separately named/versioned protocol and results. Neither existing exploratory results nor cached Set B transcripts were inspected to develop this scoring protocol. The user had already shared the exploratory review, so the broader Set B history is not a pristine first exposure; report this provenance when publishing.

## Extraction and calls

Prisma: original M4A, model=prisma-v3.0, language_code=hi-IN,en-IN, format=transcribe. previous_text is the fixed question text. Symptoms keyterms apply to P2/P4/F; medicine keyterms to P5/R1. Cache by exact audio hash and parameters.

Groq: configured model, temperature 0, json_object, existing prompt unchanged. All 212 clips have schemas (P0–P7, F, R1). Follow-up question_key is included in the LLM cache key. Same-day duration 0 is permitted by a Set B-specific validation option for all P3 clips, independent of session truth; only S03 accepts 0 or 1 in scoring. Other evaluators retain positive-duration validation. Validation errors affect their own fields, not the whole answer. Raw LLM responses and per-field errors are retained.

Allergy/condition none/unknown normalization occurs in code, without changing the prompt. Empty lists and none/no/koi nahi lists normalize to none; unknown/pata nahi/don't know lists to unknown. Mixed lists keep real names only. A sentinel-only list containing both classes becomes unknown. Verbatim evidence is still required for every non-null value.

429 is a transport state, not invalid_llm_output. Groq observes x-ratelimit-* and retry-after, paces requests/tokens conservatively and retries at most five times (six attempts). Minute-limit exhaustion after five retries aborts and resumes from cache/checkpoint; it never invents a failed extraction. A daily-quota 429 instead checkpoints and exits cleanly immediately, reporting the pending clip, last completed clip and server-reported reset timestamp (UTC and IST). It does not sleep for hours. Missing reset information is explicitly unknown; no midnight reset is assumed. A proactively exhausted daily request header also triggers a clean stop. All attempts are logged. Standard Groq request headers refer to per-day limits, token headers to per-minute limits (https://console.groq.com/docs/rate-limits). RPM/TPD are not assumed to equal public defaults when absent; the local conservative RPM pacing cap is 30, configurable via GROQ_PACING_RPM. Unknown daily quotas can still require a reset wait after 429. Pacing does not control another client using the same organization.

## Follow-up mapping and ground-truth coverage

The user's tm order is used exactly. ch keeps approved numbered files. Original semantic filenames, matched by SHA-256 in the pre-copy inventory, show ch S03 F1=pain score/F2=location and ch S04 F1=breathlessness/F2=phlegm. These are intentionally opposite tm's question order, without changing destination row names. S02 uses last BP, location, pain score in that order; other numbered ch rows follow the approved sequence.

A measured-temperature question may contain both measured and temperature. F's validated measured boolean is retained, and a deterministic parser extracts the sole plausible 80–115 Fahrenheit number, or converts an explicitly Celsius-labelled number, from that answer. An explicit number in this measurement question uses the Fahrenheit convention; absent/ambiguous temperatures remain unclear. No extra LLM request is made. S10's denial remains measured=false with no inferred temperature.

The user supplied S02 pain location = back of head OR near neck, and pain score = 5, for both speakers. Either location is accepted; the score must equal 5. Ground truth and complete-record scoring now cover all 20/20 sessions.

Ground truth follows test-scripts.md Set B with the user's sex and duration instructions: ch male/tm female; S03 accepts 0 or 1 day; S09 one day; S10 corrected four days. Three months is operationalized as 90 days before the run. S05 frequency accepts any numeric value from 5 through 6. S03 location requires left-arm radiation. S04 phlegm requires present=true and yellow/yellowish (English/Hinglish/Hindi variants). S07 location requires right knee; S08 front of head/forehead/frontal. Other numeric follow-up facts are exact and booleans remain booleans.

## Patient records and scoring

Every field is assembled with value/status/evidence. P0 token, P1 age/sex, P3 duration, allergies and conditions require status=ok plus exact values, with list order ignored and name case/spacing/transliteration normalized. The fixed absence normalization applies before validation.

Complaint is scored against every expected symptom/reason in the table, across summary and symptoms; the predeclared English/Hinglish/Hindi concept patterns live in run_setB.py. Negated mentions do not satisfy a concept. S02 requires BP-check reason and frequent headaches, S05 loose motions and one vomiting episode, S06 sugar-check reason and fatigue, S09 left arm/hand weakness and difficulty speaking. These rules are deterministic, with no grading LLM.

Follow-up accuracy means all known follow-up facts in the session are correct. Individual follow-up comparisons are also saved/reported; missing/invalid values are wrong. S09 has no follow-ups and satisfies its empty expected set.

Medicines are independently measured with fuzzy matching off and on (rapidfuzz ratio >=85; no post-run alias additions). Unknown name retains purpose BP. Names are matched one-to-one; unexpected extra names fail session-level medicine accuracy. Strength is required only when specified in the card and must belong to the correct matched medicine. The summary reports session-level all-names/all-names-and-strengths accuracy plus per-medicine names and strength-bearing name+strength counts. No drug equivalence is inferred (e.g. Aspirin does not silently equal Ecosprin). The raw baseline permits existing deterministic case/script/number/spacing normalization but no fuzzy matching.

The final record uses fuzzy candidates supported by the P5 transcript and a valid P5 status; invalid LLM fields are not accepted. R1 explicit agreement confirms candidates. Explicit disagreement applies named corrections, or a dose-only correction when exactly one candidate exists; ambiguous corrections remain unclear. A correction requires another confirmation and is labelled accordingly. Confirmation state is saved in the record; no R1 ground-truth agreement is invented from the cards. Raw/fuzzy metrics use the same correction procedure. No-result matches cannot be rescued by guessed LLM medicine names.

Red flags are session-level OR across P2/P4/F keyword/LLM/fail-safe results. A later denial cannot clear an earlier alert. P4 blood fail-safe remains enabled. needs_check counts as an alert, including false alarms on expected-negative sessions. Report positives caught x/4 overall (x/2 per speaker) and false alarms x/16 (x/8 per speaker). Expected-positive sessions are S03 and S09 only.

silently_wrong: wrong field with status=ok. safe_miss: wrong field with status unclear/declined/needs_check. Questions are reported as wrong but not counted in safe_miss, following the existing metric definition. invalid_llm_output counts clips with one or more actual validation errors, per speaker and overall; transport errors are excluded. Complete-record accuracy requires all final scored fields correct, including fuzzy medicines names and strengths and session red flag; raw matching is a baseline and does not constrain the final record.

## Failure attribution

The run prints every failed field for both speakers, row(s), transcript and expected/got. Causes are provisional: validation diagnostics -> invalid output; expected facts supported in transcript -> extraction; missing/wrong facts -> STT candidate; unimplemented/ambiguous literal checks -> scoring review. These labels are not a substitute for listening: without audio replay a recording/card mismatch can resemble STT error. No diagnostic label changes a numeric score automatically. Follow-up subfield and aggregate failures are both visible.

## Freeze, resume and authorization

The protocol JSON hashes code, ground truth, scoring notes, keyterm lists, prompt configuration, approved mapping and every recording, and records model/settings. Preflight verifies it, computes exact STT misses and known LLM misses/cache hits, and gives an upper bound for LLM calls dependent on new STT transcripts. No real calls occur in default mode. --real also requires typing RUN FULL SET B. Checkpoints live in cache/ and store only completed clips under the same protocol hash; raw provider responses use existing individual caches. Retry attempts are additional to the displayed logical-call budget. Do not run at this stage: stop at the user's call-count gate.

## User-authorized run completion changes

Before the official full run, S02 truth was completed as above. Progress is printed every 10 completed clips and at the final clip: count, cumulative elapsed seconds and Prisma/Groq HTTP attempts across resumes. Each completed clip is checkpointed. If quota is hit after Prisma succeeds, that pending clip's STT remains cached; a rerun skips completed clips and reuses the pending cached STT. Daily-quota stops return normally with status saved as daily_quota_stopped, not a scoring failure. Re-run .venv/bin/python eval/run_setB.py --real after the reported reset.
