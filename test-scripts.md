# Test Recording Scripts

**Speakers:** Chill (code `ch`) and teammate (code `tm`). If possible, add 1–3 extra voices, ideally an older relative, for **Set A only**. Get their consent first.

## How many tests

| Set | What it tests | Per speaker | 2 speakers |
|---|---|---|---|
| A: Medicines | Medicine names, keyterms on vs off | 20 clips | 40 clips |
| B: Full sessions | Question-level transcription/extraction and red flags | 10 sessions (9–12 recordings each; current `tm` batch: 106) | 20 sessions (about 212 at current batch size) |
| C: Edge cases | Unclear, declined, negation, noise, etc. | 12 clips | 24 clips |
| **Total** | | ~138 clips (106 Set B files in current tm batch) | **~276 clips at current Set B batch size** |

Planned comparison conditions: clean and phone + noise; Set A also compares keyterms off vs on. The current Set B evaluator runs the original clean recordings only; it does not create phone/noise variants or exercise the live multi-turn app flow. See [Set B run guide](eval/setB_README.md). Estimated cost: about ₹40–60.

## Recording rules (important)
1. **Don't read the card word for word.** Glance at the facts, look away, and say it the way a patient would. Hesitations, "umm", and Hindi-English mixing are good. This is what makes the test honest.
2. **One answer per file.** Keep each under 30 seconds (most will be 3–10).
3. **Use a phone mic**, at normal distance, in a normal room. For Set C item C10, turn a TV or fan on loud.
4. **Say numbers the natural way.** Mix it up: sometimes Hindi ("chaalis"), sometimes English ("forty").
5. **Your sex is your own.** Answer P1 with your actual sex; the age comes from the card.
6. **File names:** for Sets A/C, `{speaker}_{card}.wav`; for Set B, `B_{session}_{question}.m4a`, e.g. `B_S03_P4.m4a`, `B_S03_F01.m4a`, `B_S03_R1.m4a`. Set B session IDs are `S01`–`S10`; follow-ups are numbered `F01`, `F02`, etc. The `eval/setB_recording_name_map.csv` manifest preserves the original follow-up labels. Current Set B evaluator input is the teammate's `raw/setB_tm/` folder; see [Set B run guide](eval/setB_README.md).
7. **Storage:** keep recordings **out of the public repo** (voice is personal data). Share them through a private Google Drive folder. `recordings/` is already in `.gitignore`.

Easiest approach: ask Codex for a **recording mode** in the app that shows the card, plays the question, records your answer and saves it with the right file name automatically (prompt at the end).

---

## Set A: Medicine answers (20 cards)
Question being answered: P5, "Kya aap abhi koi dawai le rahe hain? Naam bataiye."

| ID | Facts to convey | Ground truth | What it tests |
|---|---|---|---|
| M01 | Telma 40, once daily | Telma 40 | Brand + Hindi number |
| M02 | Dolo 650 for fever | Dolo 650 | Large spoken number ("chhe sau pachaas") |
| M03 | Glycomet 500 and Thyronorm 50 | Glycomet 500; Thyronorm 50 | Two meds, two strengths |
| M04 | Pan 40 before breakfast, Ecosprin 75 at night | Pan 40; Ecosprin 75 | Two meds with timing words |
| M05 | Amlong 5 | Amlong 5 | Short brand name |
| M06 | Metformin and Atorvastatin (generic names) | Metformin; Atorvastatin | Generic names |
| M07 | Montair LC tablet and Asthalin inhaler (pump) | Montair LC; Asthalin | Brand with letters, "pump" |
| M08 | Shelcal and Uprise D3 (calcium, vitamin D) | Shelcal; Uprise D3 | Supplements |
| M09 | Only Thyronorm 25 | Thyronorm 25 | Single med |
| M10 | Janumet and Ecosprin | Janumet; Ecosprin | Similar-sounding brands |
| M11 | A BP tablet, name forgotten; also Pantocid | BP medicine (name unknown); Pantocid | Unknown name → purpose |
| M12 | Combiflam sometimes for pain | Combiflam | Occasional use |
| M13 | Azithral 500, started 3 days ago | Azithral 500 | Antibiotic + duration noise |
| M14 | Crocin and Cetzine for cold | Crocin; Cetzine | Cold meds |
| M15 | Rosuvas 10 and Clopilet 75 | Rosuvas 10; Clopilet 75 | Hard names, two strengths |
| M16 | Two sugar tablets: one is Glycomet, other's name forgotten | Glycomet; sugar medicine (name unknown) | Partly known |
| M17 | Budecort inhaler and Deriphyllin | Budecort; Deriphyllin | Rare names |
| M18 | Lantus insulin injection and Glycomet | Lantus; Glycomet | Injection + tablet |
| M19 | Not taking any medicine | none | Empty answer |
| M20 | Say Telma first, then correct yourself: it's actually Amlong | Amlong (not Telma) | Self-correction |

---

## Set B: Full patient sessions (10 sessions, S01–S10)
Answer every question the app asks, using the card's facts in your own words. If the app asks a follow-up that isn't covered, answer naturally and consistently with the card, and note what you said.

**S01: Fever**
- Token 12 · Age 34
- Complaint: fever with body ache · Duration: 3 days
- Follow-ups: measured 101°F; chills yes
- Red flags: none
- Medicines: Dolo 650 · Allergies: none · Conditions: none

**S02: BP check**
- Token 7 · Age 58
- Complaint: BP check, frequent headaches · Duration: 1 week
- Follow-ups: last BP 150/95
- Red flags: none
- Medicines: Telma 40, Amlong 5 · Allergies: none · Conditions: BP

**S03: ⚠ Chest pain (RED FLAG)**
- Token 21 · Age 62
- Complaint: chest pain and heaviness · Duration: since this morning
- Follow-ups: pain 8/10, spreading to left arm
- Red flags: **YES**, chest pain and breathlessness (answer yes at P4)
- Medicines: Ecosprin 75, Atorva · Allergies: none · Conditions: sugar, BP
- Expected: the app interrupts with the red-flag alert

**S04: Cough**
- Token 3 · Age 27
- Complaint: cough · Duration: 5 days
- Follow-ups: yellow phlegm; no breathlessness
- Red flags: none
- Medicines: Asthalin inhaler · Allergies: **Augmentin** (got a rash) · Conditions: asthma

**S05: Stomach**
- Token 15 · Age 41
- Complaint: loose motions, vomited once · Duration: 2 days
- Follow-ups: 5–6 times a day
- Red flags: none
- Medicines: ORS, Thyronorm 50 · Allergies: none · Conditions: thyroid

**S06: Sugar follow-up**
- Token 9 · Age 49
- Complaint: sugar check, tired all the time · Duration: 2 weeks
- Follow-ups: last fasting sugar 210
- Red flags: none
- Medicines: Glycomet 500, Janumet · Allergies: none · Conditions: sugar

**S07: Knee pain**
- Token 18 · Age 55
- Complaint: knee pain · Duration: 3 months
- Follow-ups: right knee; pain 6/10
- Red flags: none
- Medicines: Combiflam sometimes, Shelcal · Allergies: "pata nahi" (unknown) · Conditions: none

**S08: Headache (negation trap)**
- Token 5 · Age 30
- Complaint: headache · Duration: 2 days
- Follow-ups: front of head; pain 5/10
- Red flags: **NO.** At P4, clearly deny: "Nahi, seene mein dard ya saans ki koi dikkat nahi hai."
- Medicines: Crocin · Allergies: none · Conditions: none
- Expected: **no** alert. This tests false alarms on negated words.

**S09: ⚠ Weakness (RED FLAG)**
- Token 23 · Age 67
- Complaint: left arm weak since yesterday, slight difficulty speaking · Duration: 1 day
- Red flags: **YES**, one-sided weakness and speech difficulty
- Medicines: Telma 40, Glycomet · Allergies: none · Conditions: BP, sugar
- Expected: red-flag alert

**S10: Messy patient**
- Token 25 · Age 55 (say it in Hindi: "pachpan")
- Complaint: fever and body pain · Duration: **say "teen din... nahi, chaar din"** (truth: 4 days)
- Follow-ups: didn't measure the fever
- Red flags: none
- Medicines: "BP ki goli, naam yaad nahi" · Allergies: none · Conditions: BP
- Expected: duration = 4 days; medicine = BP medicine (name unknown)

---

## Set C: Edge cases (12 clips)

| ID | Question | Say (roughly) | Expected |
|---|---|---|---|
| C01 | P2 | "Haan... hello? Awaaz aa rahi hai?" | unclear → app asks again |
| C02 | P1 | "Umar nahi bataunga" | age declined, not guessed |
| C03 | P5 | "Aap dawai ka naam kyun pooch rahe ho?" | treated as a question |
| C04 | P1 | "Baavan saal" | age 52 |
| C05 | P3 | "Parson se" | 2 days |
| C06 | P3 | "Pichhle hafte se" | about 7 days |
| C07 | P2 | Fully English: "Since last Monday I have a severe headache" | complaint captured |
| C08 | P4 | "Saans phool rahi hai, seedhi nahi chadh pa raha" | **RED FLAG** (breathlessness) |
| C09 | P4 | "Ulti mein khoon aaya tha kal" | **RED FLAG** (vomiting blood) |
| C10 | P2 | Any normal complaint, recorded with a TV or fan loud | complaint captured despite noise |
| C11 | P4 | "Behoshi nahi hui, bas thoda chakkar aaya tha" | **no** red flag (negation + mild symptom) |
| C12 | P2 | A long 20–25 s rambling answer with 3 symptoms (e.g. cough, fever, weakness) | all symptoms captured |

---

## Summary of red-flag tests
Expected alerts: S03, S09, C08, C09 (×2 speakers = **8**). Must-not-alert traps: S08, C11 (×2 = **4**).
Target: **0 missed red flags.** Report false alarms honestly.

---

## Codex prompt: recording mode
> Add a "Recording mode" tab to the Streamlit app. It loads test cards from `data/test_cards.yaml` (Sets A, B and C from `test-scripts.md`; convert them to YAML with ground truth). The user selects a speaker code (ch / tm / other) and a card. For Set B, it steps through the questions in order, plays the cached prompt audio, shows the card facts, records each answer, and saves one clip per question as `B_{session}_{question}.m4a` under `recordings/`. Use P0–P7, F01/F02/etc. for follow-ups, and R1 for the medicine read-back. For Sets A and C, it records one clip per card with names `{speaker}_{card}.wav`. Show a checklist of which clips are done per speaker. Never call the Gnani API in this tab.
