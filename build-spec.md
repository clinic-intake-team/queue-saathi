# Clinic Queue Intake — Build Spec (Gnani Challenge)

**One-liner:** Patients answer a short Hinglish voice intake while waiting in the clinic queue. The doctor gets a clean summary, with red flags on top, before they walk in.

**Deadline:** Nov 10, 2026, 11:59 PM IST. Submit early.
**Rule until Nov 10:** no new ideas. Write them in a parking-lot list.

---

## 1. Scope (only build this)

Fields collected:
- Token number, age, sex
- Main complaint, duration
- Up to 2 adaptive follow-ups based on the complaint
- Red-flag screen
- Current medicines (with confirmation)
- Allergies
- Existing conditions (sugar, BP, thyroid, asthma, other)

The system **only collects and summarises.** It never diagnoses or advises. If a red flag shows up, it plays one fixed message: "Kripya abhi reception par bataiye."

Out of scope: real phone line, login, patient records across visits, other languages, deployment polish.

---

## 2. Gnani API facts (from docs.gnani.ai)

**General:** Base URL `https://api.vachana.ai`. Header `X-API-Key-ID: <key>` on every request (401 means a missing or bad key). Keys come from app.gnani.ai/voice. No official Python SDK is needed: plain `requests` works.

**Speech-to-text: Prisma v3.0 (REST)**
- `POST /stt/v3`, multipart form
- Fields: `audio_file` (WAV/MP3/OGG/FLAC/AAC/M4A, 8–44.1 kHz, **max 30 s**), `model=prisma-v3.0`, `language_code=hi-IN,en-IN` (or `indic-auto`), `format=transcribe` (English words in Latin script, numbers as digits)
- **`keyterms`**: JSON array, up to 200 terms. Used for medicine names.
- `topic` (up to 1,600 chars) and `previous_text` (last 600 chars kept): pass the question just asked as context
- Response: `transcript`, `detected_language_code`, `request_id`, `processing_time`. **No word timestamps and no confidence score.**
- 8 kHz input is accepted, so phone-quality clips can be sent as they are. HTTP 429 means rate limited: retry with backoff.

**Text-to-speech: Timbre v3.0**
- `POST /api/v1/tts/inference`, JSON
- `{"text", "model": "timbre-v3.0", "voice": "Shivani", "language": "hi-en", "speed": 1.0, "audio_config": {"sample_rate": 16000, "num_channels": 1, "sample_width": 2, "encoding": "linear_pcm", "container": "wav"}}`
- Returns raw WAV bytes. Write numbers as spoken words in the text. v3.0 voices include Shivani, Avinash, Lakshmi. If v3.0 misbehaves, fall back to `timbre-v2.5` (voices: Nalini, Kaveri, etc.).
- HTTP 403 can mean credits ran out.

**Reasoning:** Evon v3.3 is not on the API (it needs a large GPU). Use Gemini (free tier) or another LLM for extraction, and **say so honestly** in the submission. Try Evon only if there's spare time.

---

## 3. Credit plan (4,900 credits left)

The docs don't publish per-call cost. **Measure it before building anything** with `step0_credit_test.py`: 2 STT calls (keyterms off/on) and 1 TTS call, noting the balance between each. Record the results in `docs/CREDITS.md`.

**Rules:**
1. **Cache every TTS output.** The question set is fixed, so generate each prompt once, save the WAV in `assets/prompts/`, and never call Timbre for it again. Only the medicine read-back is generated live.
2. **Cache every STT result** by audio file hash in `cache/stt/`. Re-running the evaluation must not re-spend credits.
3. **Mock mode:** `GNANI_MOCK=1` returns saved responses. Use it for all UI and logic work.
4. **Log every real call** to `logs/api_calls.csv` (time, endpoint, audio seconds, characters, request_id).
5. Keep clips short: trim silence before sending.

**Budget split** (adjust once Step 0 gives real costs):

| Use | Share |
|---|---|
| Step 0 cost test | ~1% |
| TTS prompt cache | ~5% |
| Integration testing | ~15% |
| Evaluation | ~40% |
| Demo recording | ~15% |
| Reserve (keep for the final demo and fixes) | ~24% |

**Keys:** credits are probably one shared pool across all keys, so more keys don't mean more credits. Use one key for development and one for evaluation, and keep the third spare. Store them in `.env`, add `.env` to `.gitignore`, and never paste a key into a Codex prompt or a commit.

---

## 4. Conversation flow (Hinglish; cache all fixed prompts)

| # | Prompt (Timbre) | Extracts |
|---|---|---|
| P0 | "Namaste! Main clinic ki taraf se kuch chhote sawaal poochungi, taaki doctor ko pehle se pata ho. Aapka token number kya hai?" | token |
| P1 | "Aapki umar kitni hai, aur aap purush hain ya mahila?" | age, sex |
| P2 | "Aaj aap kis takleef ke liye aaye hain? Apne shabdon mein bataiye." | complaint |
| P3 | "Yeh takleef kab se hai?" | duration (normalised to days) |
| F* | Adaptive follow-ups (max 2), picked by complaint type. See below. | details |
| P4 | "Kya aapko seene mein dard, saans lene mein dikkat, behoshi, ya kahin se zyada khoon aa raha hai?" | red flags |
| P5 | "Kya aap abhi koi dawai le rahe hain? Naam bataiye. Naam yaad na ho toh bataiye kis cheez ki dawai hai." | medicines |
| R1 | Live: "Maine suna: {med list}. Kya yeh sahi hai?" | confirm or correct |
| P6 | "Kya kisi dawai se aapko allergy hai?" | allergies |
| P7 | "Kya aapko sugar, BP, thyroid, asthma, ya koi aur purani bimari hai?" | conditions |
| P8 | "Shukriya! Aapki jaankari doctor tak pahunch gayi hai. Apni baari ka intezaar kijiye." | — |
| RF | Fixed alert: "Yeh zaroori lag raha hai. Kripya abhi reception par bataiye." | — |
| RP | Unclear answer: "Maaf kijiye, theek se samajh nahi aaya. Ek baar phir bataiye?" (max 1 retry, then mark "not recorded") | — |

**Follow-ups by complaint type** (the LLM classifies the complaint, the code picks the question):
- Fever: "Bukhaar naapa tha? Kitna tha?" / "Thand lag ke aata hai?"
- Pain: "Dard theek kahan hai?" / "Ek se das mein dard kitna tez hai?"
- Cough or cold: "Balgam aata hai? Kis rang ka?" / "Saans phoolti hai?"
- Stomach: "Ulti ya dast ho rahe hain? Din mein kitni baar?"
- Sugar/BP follow-up visit: "Pichhli baar sugar ya BP kitna aaya tha?"
- Other: "Thoda aur bataiye, kya kya ho raha hai?"

**Red flags, two layers (either one triggers RF):**
1. A keyword list in code (Hindi, Hinglish and English): seene mein dard / chest pain, saans nahi aa rahi, behosh, daura / jhatke, ek taraf kamzori / muh tedha, bolne mein dikkat, khoon ki ulti, kaala mal, bahut zyada khoon, garbhavastha + khoon/dard, gardan akadna + tez bukhaar.
2. An LLM flag from the extraction.

**Verify this list against an official triage or emergency-signs source before the demo, and cite it.**

---

## 5. Medicine handling (the speech-specific contribution)

1. Pass `keyterms` = the medicine list below to Prisma on the **P5 and R1 answers only**.
2. After transcription, fuzzy-match each word or phrase against the list (rapidfuzz, score ≥ 85). Strength is spoken as a number ("Telma chaalis" → Telma 40).
3. If a name matches with a low score, or nothing matches, ask: "Kya aap {best guess} keh rahe the?" Otherwise mark it "unclear: '{heard text}'".
4. If the patient doesn't know the name ("BP ki goli"), record the *purpose* instead: "BP medicine (name unknown)".

**Starting keyterm list (common Indian brands and generics; extend and verify):**
Dolo 650, Crocin, Calpol, Paracetamol, Combiflam, Brufen, Zerodol, Telma, Telma H, Telmisartan, Amlong, Amlodipine, Losar, Cilacar, Concor, Met XL, Glycomet, Metformin, Janumet, Istamet, Galvus Met, Glimisave, Amaryl, Gemer, Insulin, Lantus, Huminsulin, Thyronorm, Eltroxin, Thyroxine, Pan 40, Pantocid, Pantoprazole, Omez, Razo, Rantac, Ecosprin, Aspirin, Atorva, Atorvastatin, Rosuvas, Storvas, Clopilet, Montair LC, Allegra, Cetzine, Levocetirizine, Asthalin, Budecort, Deriphyllin, Duolin, Azithral, Azithromycin, Augmentin, Taxim-O, Ciplox, Shelcal, Uprise D3, Becosules, Neurobion Forte, Limcee, ORS, Digene, Cremaffin, Ondem, Meftal Spas, Cyclopam, Eptoin, Levipil

**Experiment:** keyterms off vs on, measured by medicine-name accuracy. This is your headline result.

---

## 6. Architecture (keep it simple)

- **Streamlit app**, two tabs:
  - *Patient:* plays the cached prompt, records the answer with `st.audio_input`, moves through the flow
  - *Doctor:* list of tokens. Each summary shows red flags (red) at the top, then complaint, duration, medicines (confirmed / unclear), allergies, conditions, and a link to the audio for each field.
- `gnani.py`: STT and TTS clients with retry and backoff, caching, mock mode, call logging
- `extract.py`: LLM to strict JSON per answer (`value`, `status`: ok / unclear / declined / question, `evidence`: quoted words). **Code validates** (age 0–110, duration parses, etc.). The LLM never writes directly to the record.
- `flow.py`: deterministic state machine (P0…P8, follow-up choice, one retry, RF interrupt)
- `meds.py`: keyterm list, fuzzy match, confirmation logic
- `redflags.py`: keyword layer plus LLM flag
- `phone_sim.py`: telephone band-pass, downsample to 8 kHz, add background noise at a set SNR (for evaluation)
- `eval/`: runner scripts plus result CSVs
- Storage: SQLite or JSON files. Synthetic data only.

---

## 7. Evaluation (how you beat the visible entries)

**Data:**
- 30 synthetic patient cards with ground truth (complaint, duration, medicines, allergies, conditions, red flags yes/no). About 6 should include a red flag.
- 4–5 consenting speakers (friends, family), each reading cards **in their own words, not a script**. Mix of ages if possible. Collect written consent and don't publish their voices without permission.
- Each clip under 30 seconds. Name files `card{id}_{speaker}_{field}.wav`.

**Eval A: medicine names (speech-specific)**
- ~40 medicine-answer clips × {keyterms off, on} × {clean, phone + noise}
- Metric: % of medicine names correctly identified, measured at each stage: raw Prisma → + keyterms → + fuzzy match → + confirmation

**Eval B: end-to-end intake**
- ~10 full sessions, clean and phone + noise
- Metrics: field accuracy per field, red flags caught (aim: 0 missed) and false alarms, average number of questions, % of fields marked "not recorded"
- Also run the extraction on hand-typed perfect transcripts, to split errors into "Prisma misheard" vs "extraction got it wrong"

**Credit check:** about 160 STT calls for Eval A and about 160 for Eval B. Scale down if Step 0 shows they're expensive (for example, run phone + noise on half the clips).

**Report:** one results table, a breakdown of where errors came from, 3 real failure examples, and a limitations section.

---

## 8. Build order

1. Step 0 credit test
2. `gnani.py` (cache, mock, logging) and cached prompts
3. Flow, extraction and red flags, working in mock mode
4. Medicines and keyterms
5. Patient and doctor UI, then first real end-to-end session
6. Record the test set and run the evaluation
7. README, demo video, posts, submission

Public posts along the way: (1) the problem, (2) a short clip plus one Prisma finding, (3) the 60-second demo with numbers. Nominate the third.

---

## 9. Codex prompts (paste one phase at a time)

**Phase 1: skeleton and API client**
> Create a Python project `clinic-intake` with Streamlit. Add `gnani.py` with two functions: `stt(wav_path, keyterms=None, context=None)`, which POSTs to `https://api.vachana.ai/stt/v3` (multipart; fields `audio_file`, `model=prisma-v3.0`, `language_code=hi-IN,en-IN`, `format=transcribe`, optional `keyterms` as a JSON array, optional `previous_text`); and `tts(text, out_path)`, which POSTs JSON to `https://api.vachana.ai/api/v1/tts/inference` with `model=timbre-v3.0`, `voice=Shivani`, `language=hi-en`, and audio_config of 16000 Hz mono 16-bit linear_pcm WAV, then writes the returned bytes to a file. Read the API key from `.env` (`GNANI_API_KEY`) with the header `X-API-Key-ID`. Requirements: cache STT results by SHA-256 of the audio bytes plus parameters in `cache/stt/*.json`; skip TTS if `out_path` exists; retry on 429/500/503 with exponential backoff (max 3); log every real call to `logs/api_calls.csv` (timestamp, endpoint, audio_seconds, chars, request_id, status); if the `GNANI_MOCK=1` env var is set, return canned responses without network calls. Add `.gitignore` for `.env`, `cache/`, `logs/`, `recordings/`. Add a script `scripts/generate_prompts.py` that renders every fixed prompt in `prompts.yaml` to `assets/prompts/{id}.wav` once.

**Phase 2: flow and extraction**
> Add `flow.py`: a deterministic state machine over prompt IDs P0–P8 with up to 2 follow-ups chosen by complaint category (fever, pain, cough_cold, stomach, chronic_followup, other), one retry on unclear answers (then mark "not recorded"), and an immediate RF alert state if a red flag is detected. Add `extract.py`: call an LLM (configurable; default Gemini via `GEMINI_API_KEY`) with the current question and transcript, and return strict JSON `{field: {value, status in [ok, unclear, declined, question], evidence}}`. Validate in code: age 0–110, duration normalised to days, sex in [male, female, other, unknown]. Never accept LLM values without validation. Add `redflags.py` with a Hindi/Hinglish/English keyword list plus the LLM flag; either triggers RF.

**Phase 3: medicines**
> Add `meds.py`: load `data/medicines.txt`, pass it as `keyterms` for medicine questions, then fuzzy-match transcript phrases with rapidfuzz (threshold 85), parse spoken strengths ("chaalis" → 40), and return confirmed / needs_confirmation / unknown_name_with_purpose. Generate the read-back sentence for TTS.

**Phase 4: UI**
> Streamlit app with Patient and Doctor tabs. Patient: play the cached prompt audio, record with `st.audio_input`, run STT → extract → flow, show progress. Doctor: list sessions by token; summary card with red flags in red at the top, then complaint, duration, follow-up details, medicines (confirmed vs unclear), allergies, conditions; each field shows the evidence quote and a playable clip. Store sessions as JSON in `data/sessions/`.

**Phase 5: evaluation**
> Add `phone_sim.py` (telephone band-pass 300–3400 Hz, resample to 8 kHz, mix noise from `data/noise/*.wav` at a given SNR; keep the output at 8 kHz since Prisma accepts it). Add `eval/run_meds.py` and `eval/run_e2e.py` that read `data/cards.csv` (ground truth) and `recordings/`, run each condition through the cached STT, and write per-clip and summary CSVs: medicine accuracy by stage, field accuracy, red flags missed and false alarms, questions per session, % not recorded, and an error attribution comparing STT vs extraction (by also running extraction on typed gold transcripts in `data/gold_transcripts.csv`).

---

## 10. Submission checklist
- [ ] Models named: Prisma v3.0 (STT, with keyterms), Timbre v3.0 (TTS), LLM used for extraction (named honestly)
- [ ] Demo video ≤ 60 seconds, opening with the patient's problem
- [ ] Written explanation: problem, user, how it works, results table, limitations, safety statement
- [ ] Public repo with README, no keys, no real personal data
- [ ] LinkedIn and X posts live, tagging Gnani AI, with #GnaniAI and #GreatIndianAIInternshipChallenge, nominated
- [ ] Each member's contribution stated (if solo, say so)
