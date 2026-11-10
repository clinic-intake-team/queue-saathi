> Historical development handoff. For the current web app, start with [SETUP.md](SETUP.md).

# Clinic Queue Intake — teammate / Antigravity handoff

Updated: 6 November 2026 (IST). This is a project handoff, not permission to spend API credits, alter evaluation rules, or publish files automatically.

## 1. Start here

You are continuing an existing Python project. Work in the existing `Gnani_Hackathon` repository root. Do not create a second project folder such as `clinic-intake/`.

Read this handoff and inspect the actual implementation before editing. Prefer the current code and `eval/SCORING_NOTES.md` over stale descriptions in the original README. Ask the user to approve concrete call counts before running any new real API evaluation. No API calls were made to prepare this handoff.

Repository: https://github.com/clinic-intake-team/Gnani_Hackathon

At handoff inspection, local `main` was at `4b3cb8b` (`Add Set B teammate recordings`), following `574755f` (Set C audio sharing) and `4e53a85` (Set C evaluation code/results). These are a point-in-time reference; inspect Git for later changes.

The source build specification is `build-spec.md`; recording cards are in `test-scripts.md`. The submission deadline specified by the project is **10 November 2026, 11:59 PM IST**. Keep to the existing scope and put new ideas in a parking lot.

## 2. Product and scope

Patients answer short Hinglish voice questions while waiting in a clinic queue. The doctor should receive a structured summary, with red flags first, before the consultation.

The system collects and summarizes. It must not diagnose or give treatment advice. Synthetic patient scenarios are used for evaluation. A red flag or an incomplete safety screen must trigger reception/recheck handling rather than a reassuring negative result.

Target intake fields:

- Token, age, sex.
- Complaint, duration, up to two deterministic complaint-specific follow-ups.
- Red-flag screen.
- Current medicines, including read-back confirmation.
- Allergies and existing conditions.

The full planned flow is P0 token → P1 age/sex → P2 complaint → P3 duration → up to two follow-ups → P4 red flags → P5 medicines → dynamic medicine read-back → P6 allergies → P7 existing conditions → P8 close. Red flags can interrupt the flow. Unclear answers get at most one retry before being marked not recorded. See `build-spec.md` for fixed wording and the precise original scope.

Real phone lines, account/login systems, longitudinal patient records, additional languages and deployment polish are outside the agreed scope.

## 3. Implemented files and remaining work

| File / directory | Current role |
|---|---|
| `gnani.py` | Prisma STT and Timbre TTS; mock default, explicit real-call guard, caches, retries, API attempt logs, WAV/M4A duration helpers. |
| `llm.py` | Groq provider, JSON mode, temperature zero, explicit real-call opt-in, rate spacing, retries and attempt logs. |
| `extract.py` | P1–P5 extraction, validation by field, response/diagnostic caching. |
| `redflags.py` | Keyword layer, LLM symptom layer and conservative P4 fail-safe. |
| `data/medicines.txt` | 69 medicine keyterms from the original spec. |
| `data/symptoms.txt` | 34 fixed English/Hinglish symptom keyterms. |
| `data/setA_ground_truth.csv` | 20 medicine cards. |
| `data/setC_ground_truth.csv` | 12 edge-case cards, shared by both speakers. |
| `eval/run_meds.py` | Set A raw-STT medicine recognition comparison. |
| `eval/run_setC.py` | Set C development evaluation, symptom keyterms off/on. |
| `eval/SCORING_NOTES.md` | Authoritative Set C version-2 scoring, safety and cache policy. |
| `eval/results/` | Real evaluation CSVs; older Set C baseline retained as `_v1.csv`. |
| `eval/*protocol*.json`, `examples/*protocol*.json` | Historical/current protocol fingerprints. Do not silently bypass mismatches. |
| `scripts/step0_credit_test.py` | Interactive cost measurement; exactly three POST attempts, no retries. Do not rerun casually. |
| `scripts/generate_prompts.py` | Fixed prompt audio generation; silent offline placeholders by default. |
| `scripts/setup_groq.py` | Explicit model listing and setup completion test. Already performed; not a routine startup step. |
| `scripts/test_extraction_examples.py` | Eight independently authored development examples; real access requires `--real`. |
| `prompts.yaml` | Prompt text for P0–P8, RF, RP and fixed follow-ups. |
| `app.py` | Only a Streamlit Patient/Doctor tab skeleton. Not a functioning intake UI. |
| `tests/` | Last verified suite: 23 offline tests passing. |

**Not implemented yet:** deterministic `flow.py`, dedicated `meds.py` confirmation pipeline, full patient/doctor UI, session persistence, phone/noise processing, Set B ground truth/runner and complete end-to-end evaluation.

**Extraction coverage gap:** `extract.py` currently supports only P1, P2, P3, P4 and P5. There is no token/P0, adaptive follow-up, allergy/P6 or conditions/P7 extractor yet. P8 is closing audio, not a patient field. A Set B runner must not pretend these missing fields already work.

## 4. Local setup and secrets

From the repository root:

```bash
git pull origin main
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
# Only create .env if it does not already exist:
test -f .env || cp config/env.example .env
python -m unittest discover -s tests -v
```

Configure `.env` locally; never paste real secrets into an AI prompt or commit them:

```dotenv
GNANI_MOCK=1
GNANI_API_KEY=<your-current-key>
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b
GROQ_API_KEY=<your-current-key>
```

The model selected from the actual Groq model list was `openai/gpt-oss-120b`. The key did not expose a Llama 70B+ chat model at setup time. Do not describe the extraction model as Llama, Gemini or Gnani Evon. Keep the model configurable and name the actual provider/model honestly.

The existing `.venv` on Sagar's machine used Python 3.15, but a teammate should create their own environment. Do not copy `.venv` between machines. Dependencies are `requests`, `python-dotenv`, PyYAML and Streamlit; no Gemini dependency is in the active path.

An earlier `.env` containing a Gnani key was pushed, then removed from reachable repository history with `git filter-repo` and force-pushed. This handoff does not establish whether the old key was revoked. Use replacement keys and never reintroduce old history. `.env` is currently ignored and not tracked.

## 5. API behavior and operating safeguards

### Gnani

- Base: `https://api.vachana.ai`; header `X-API-Key-ID` from `GNANI_API_KEY`.
- STT: `POST /stt/v3`, multipart `audio_file`, `model=prisma-v3.0`, `language_code=hi-IN,en-IN`, `format=transcribe`.
- Keyterms are a JSON array of at most 200 strings.
- Pass the question text as `context`; the client sends its last 600 characters as `previous_text`.
- Clips must be under 30 seconds. Send original M4A recordings directly to Prisma for clean evaluation.
- Prisma can emit Hindi number words, English number words or digits for the same audio. There is no word confidence score to use as a threshold.
- TTS: `timbre-v3.0`, Shivani, `hi-en`, 16 kHz mono 16-bit WAV.
- `GNANI_MOCK` defaults to `1`. Mock STT is canned data, not real transcription. Its fixtures reproduce the Step 0 Telma/Glycomet transcripts.
- Real client access requires `GNANI_MOCK=0` and explicit script opt-in (`gnani._REAL_SCRIPT`). Evaluation runners handle this only after their confirmation gate.
- STT cache: SHA-256 of audio bytes plus request parameters and mock/real mode, under `cache/stt/`. Changing keyterms/context intentionally creates a distinct request.
- Real attempts, including retries/errors, go to `logs/api_calls.csv`.
- HTTP 429/all 5xx: exponential backoff, up to three total attempts. Transport errors are not silently retried; redirects are not followed.
- TTS mock WAV files are silent placeholders marked with `.wav.mock`. Real prompt generation replaces marked placeholders and reuses existing real WAV outputs.

### Groq

- Endpoint: `https://api.groq.com/openai/v1/chat/completions`.
- Uses `GROQ_API_KEY`, `LLM_PROVIDER` and `LLM_MODEL`.
- `temperature=0`, `response_format={"type":"json_object"}`.
- One-second spacing between calls; retries 429/5xx with exponential backoff and Retry-After handling, up to three total attempts.
- Every attempt logs time/model/tokens/status to `logs/llm_calls.csv`.
- No network on import. `allow_real=True` is required for a cache miss.
- Never repeatedly call until an invalid generation passes validation.

`GNANI_MOCK=1` does **not** mock Groq. Offline LLM development must use cached responses or injected/mocked responses and keep `allow_real=False`.

## 6. Current extraction contract and safety behavior

`extract.extract(question_id, transcript, allow_real=False, details=optional_dict)` returns requested fields, each shaped as:

```json
{"value": null, "status": "unclear", "evidence": ""}
```

Extraction statuses are `ok`, `unclear`, `declined`, `question`.

- P1: `age` integer 0–110; `sex` male/female/other/unknown.
- P2: `complaint.value = {"summary": "short English summary", "symptoms": ["..."]}`.
- P3: `duration_days` positive finite number.
- P4: `red_flag_symptoms` list, empty for a usable denial.
- P5: medicines list, each `{name, strength, purpose}`; values may be null where appropriate, and unknown names retain purpose.

Validation is **per field**. A bad field becomes null/unclear and records a diagnostic; other valid fields survive. Non-null values, including empty lists, require nonempty verbatim evidence. Null-valued fields do not need a verbatim evidence quote. No unvalidated value is accepted.

Examples of normalization required by the project: `baavan` → 52, `parson se` → 2 days, `pichhle hafte se` → about 7 days. Negation and corrections must be respected. Do not guess a declined age.

LLM cache identity includes provider, model, question, transcript and system prompt. Legacy cache records/raw bodies are reused where available and revalidated. `.validated_v2.json` stores the current sanitized result and diagnostics; `.response.json` stores a captured original response body. Some historical bodies were never saved; a parsed result is not a substitute for a claimed full raw response.

`redflags.detect(transcript, result, question="P4", validation_errors=issues)` combines keywords with the LLM layer:

- Either positive layer triggers an alert.
- In P4, any non-negated blood/khoon/bleeding mention triggers an alert, even if the vomiting reference was lost.
- Invalid, unclear or incomplete P4 answers yield screen status `needs_check` and `alert=true`. Do not turn a failed screen into “no red flag”.
- `needs_check` is a screening disposition, distinct from the extraction's `unclear` status. The future app must re-ask or direct to reception.
- The broad blood rule can produce conservative alerts; keyword negation is heuristic and not a clinically validated triage system.

For a new app/Set B integration, pass the question ID explicitly and preserve validation diagnostics when calling red-flag detection.

## 7. Evaluation status and results

### Set A: medicine names

40 recordings: M01–M20 for `ch` and `tm`. Unknown medicines in M11/M16 and M19's “none” are excluded from raw name accuracy; known medicines in mixed answers remain scored. M20 ground truth is Amlong only after correction.

| Condition | Name accuracy | Name + strength accuracy |
|---|---:|---:|
| Keyterms off | 30/58 (51.7%) | 14/22 (63.6%) |
| Keyterms on | 55/58 (94.8%) | 20/22 (90.9%) |

Name+strength denominator contains only medicines with a specified strength. The raw presence metric is not a full medicine-confirmation or hallucination metric. See `eval/README.md` and `eval/results/setA_*.csv`.

### Set C: development set for BOTH speakers

Both speakers are explicitly development data now. Their failures may be inspected. These results are not held-out performance.

| Symptom keyterms | Speaker | Status | Value | Flags caught | False alarms | Silently wrong | Safe miss |
|---|---|---:|---:|---:|---:|---:|---:|
| Off | overall | 22/24 | 21/24 | 4/4 | 0/2 | 1 | 2 |
| Off | ch | 12/12 | 12/12 | 2/2 | 0/1 | 0 | 0 |
| Off | tm | 10/12 | 9/12 | 2/2 | 0/1 | 1 | 2 |
| On | overall | 23/24 | 22/24 | 4/4 | 0/2 | 1 | 1 |
| On | ch | 12/12 | 11/12 | 2/2 | 0/1 | 1 | 0 |
| On | tm | 11/12 | 11/12 | 2/2 | 0/1 | 0 | 1 |

- `silently_wrong`: status ok but wrong value.
- `safe_miss`: a value was expected, but status unclear/declined/needs_check. This name describes explicit uncertainty, not a guarantee of safety.
- C01 accepts unclear OR question.
- C07 checks the expected information across summary + symptoms, not only within one string.
- P2/P4 compare symptom keyterms off/on; P5 keeps medicine keyterms. P1/P3 are identical across conditions and reused.
- 48 output rows represent two conditions on the same 24 clips, not 48 independent samples.
- Latest re-evaluation spent 14 Prisma and 5 Groq calls, with 34 and 43 cache hits respectively, and no HTTP retries in that run.
- Remaining issues: tm_C04 age mistranscription in both conditions; off-condition tm_C09 needs_check and tm_C10 “road pain”; on-condition ch_C10 “scratchy throat” rejected by the fixed throat-pain synonym rubric. Do not silently patch this rubric to inflate the saved result.

Current files: `eval/results/setC_per_clip.csv`, `eval/results/setC_summary.csv`. The earlier baseline is preserved in `_v1.csv` files. Protocol histories are kept separately.

Dry plans (no real API calls):

```bash
python eval/run_meds.py
python eval/run_setC.py
```

Those plans depend on local audio and caches. A fresh teammate clone will not have Sagar's ignored `recordings/` copies or caches; recreate/share them privately before assuming a cheap rerun. Existing result CSVs alone do not populate provider caches.

## 8. Set B: next work, with gates

**Important:** Set B contents were deliberately not read or used while building/tuning Set C. Do not use Set B speaking lines or results to tune extraction/keywords and then claim an unbiased test. Decide and record its evaluation role with the user before opening its ground truth or running it. The next agent should build missing logic using independent synthetic examples first, freeze it, then use Set B for the agreed evaluation. If Set B is later used for development, label that honestly.

### Observed metadata only — not an assessment of recording completeness

- `raw/setB_tm/` has **106 tracked audio files**, nested inside session directories S01–S10. Looking only at `raw/setB_tm/*.m4a` will incorrectly find none.
- Example filename structure: `raw/setB_tm/S05/B_S05_P5.m4a` and an adaptive answer such as `B_S05_F(how).m4a`.
- `raw/setB_chill/` has **zero audio files locally**, including recursively. Do not invent a second speaker's results or assume those recordings exist on this machine.
- Filenames/counts were inspected for this handoff; audio and the Set B script/ground-truth content were not read.
- 106 files does not prove every required answer is present or mapped correctly. Follow-up naming, branch-dependent answers and multiple recordings must be audited.
- `ffmpeg` is not available on this inspected machine's PATH. The macOS `afinfo` duration helper is available. A teammate's environment may differ.

### Recommended continuation sequence

1. **Inspect only the implementation first.** Review `extract.py`, `redflags.py`, `gnani.py`, `llm.py`, the Set C scorer, and the new safety policy. Build missing token/follow-up/allergy/conditions support, medication confirmation and deterministic flow from independent examples. Add meaningful offline tests. Do not hardcode session answers or expected red flags into the pipeline.
2. **Agree on the Set B evaluation protocol.** Define field/status scoring, the denominators, normalizations, approximate durations, adaptive follow-up handling and early red-flag termination before viewing outputs. Record prompt/keyword/model/scorer hashes. Confirm whether only tm is currently available and whether ch will be supplied.
3. **Inventory Set B recursively.** Inspect filenames and durations without API calls. Infer session/question/speaker IDs; show the full proposed source→destination mapping, duplicates, missing questions and any >=30-second clips. A reasonable destination convention is `recordings/tm_S05_P5.m4a`, with stable follow-up IDs approved by the user. Do not assume `F(how)` unambiguously identifies a particular follow-up. **STOP for confirmation before copying.** Preserve originals and extension, never overwrite a conflicting file.
4. **Create ground truth after protocol agreement.** Use the authorized Set B section of `test-scripts.md` and, only when needed/authorized, Set B speaking lines. Prefer a new `data/setB_ground_truth.csv` or explicitly structured equivalent. Keep facts separate from transcripts. Do not change expectations to match what Prisma or the LLM returned. Missing answers remain missing; do not synthesize recordings.
5. **Implement `eval/run_setB.py` (or clearly named end-to-end runner).** Load actual recordings, obtain STT with the question as previous_text, use symptom keyterms on P2/P4 and medicine keyterms on P5 according to the frozen plan, then validated extraction, safety detection and flow/session aggregation. Handle token, follow-ups, allergies and conditions explicitly; the current extractor alone cannot do full sessions. Never put ground-truth values into STT context or LLM prompts.
6. **Distinguish two tasks.** Per-field replay of prerecorded answers measures extraction; deterministic traversal/early interruption measures end-to-end flow. Do not call replay a live conversation. For early alerts, exclude or separately label later prerecorded answers rather than processing them and claiming the flow interrupted correctly. Report keyword/LLM alerts separately from needs_check referrals.
7. **Metrics:** field/status accuracy by field and speaker, red flags caught/missed, false alarms, needs_check/referrals, silently_wrong/safe_miss, not-recorded rate, questions processed, and available latency. Freeze denominators for missing/not-asked questions. If comparison on hand-typed gold transcripts is planned, get user-provided/authorized transcripts; do not invent them. Do not report mock results as real measurements.
8. **Call-count gate.** Hash actual audio + all parameters, count exact STT cache misses, count known LLM misses and an upper bound for unknown transcripts. Print retry ceilings and expected spend/calls. **STOP for explicit confirmation before any real API calls.** There is no approved Set B call count yet; do not quote a made-up total from 106 files.
9. **Run only after confirmation.** Reuse caches; log every attempt; capture raw LLM responses before validation. Fail a single field safely without discarding other validated fields. Never retry invalid output until it becomes correct. Preserve baseline CSVs and print the agreed speaker detail policy.
10. **Report before tuning.** Categorize failures as STT, extraction, validation or ambiguity/rubric mismatch. Ask before changing frozen prompts, keywords, rules or scoring after results. Keep a clean before/after record if the user authorizes development changes.

## 9. Audio, Git and local-only artifacts

The project originally ignored all voice data. The user later explicitly approved pushing Set A, Set B and Set C recordings for easier teammate sharing. Those committed files are accessible to anyone with repository access. `.gitignore` still ignores **new** raw audio; already-tracked recordings remain tracked.

- `raw/`: source recordings; may include tracked audio added explicitly. Preserve originals.
- `recordings/`: normalized filename copies, ignored.
- `cache/`, `logs/`, `.venv/`, `.env`: ignored. Never force-add them.
- Raw folder structure/README/placeholders are tracked via ignore exceptions.
- Share caches privately if avoiding duplicate paid calls matters; do not publish keys or raw model logs as a side effect.

If a teammate cannot see a file, verify it was actually committed and pushed, not just present locally. `git pull` does not transfer ignored local caches, `.env`, or uncommitted recordings. New voice-data publication requires explicit user authorization; the existing history is not a blanket instruction to add everything.

Useful checks:

```bash
git status --short
git ls-files raw/
git check-ignore .env recordings/example.m4a raw/example.m4a
```

Do not use `git add -A` blindly. Stage explicit code/data/results files, inspect `git diff --cached --stat`, then commit. Do not force-push or rewrite history as a routine collaboration step.

## 10. Additional implementation pitfalls and unfinished submission work

- The root README still describes a Phase 1 skeleton and includes outdated notes about tracked `.env` and narrower retries. This handoff/code supersede those points; updating the README is future work.
- `eval/setC_README.md` describes version 1; it links to current `SCORING_NOTES.md`.
- `prompts.yaml` currently has an RP value containing trailing textual instructions from the original table parsing. Fix/verify it before generating real retry audio; do not change evaluation question contexts silently. The current Set C runner only uses P1–P5.
- Prompt WAV files may be silence from mock generation. Verify audio/sidecars before a real demo.
- Medicine recognition evaluation is not medicine confirmation. A dedicated confirmation path still needs implementation.
- Do not normalize Hindi numbers by assuming Prisma always emits digits.
- Broad blood and negation rules need independent testing and the spec's requested official emergency-sign citation before a demo. Existing test success is not clinical validation.
- For later phone/noise experiments, first decode M4A to 16-bit mono WAV with ffmpeg. Do not send a byte-renamed M4A as a WAV. Downsample/process only after correct decoding; retain originals.
- Check `docs/CREDITS.md` for the observed Step 0 costs; balances/pricing may have changed. Do not query keys or credit balances automatically.
- Final deliverables still include full workflow/UI, end-to-end results, failure examples/limitations, README, <=60-second demo and submission material. Models must be named as actually used.

## 11. Suggested first message to Antigravity

> Read TEAMMATE_HANDOFF.md and inspect the existing code. Continue in this repository root. Start by auditing missing extraction fields, flow and Set B evaluation infrastructure using your own synthetic examples only. Do not read Set B speaking lines, ground truth or audio content until we agree the protocol. You may inventory filenames and durations, but show a full copy mapping and stop before copying. Keep GNANI_MOCK=1; do not make real Gnani or Groq calls without an explicit call-count gate and my confirmation. Preserve existing results and protocol history. Do not commit secrets or automatically publish voice data. Give me the concrete next implementation plan and the gaps you verified.
