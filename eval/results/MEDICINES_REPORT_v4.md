# Medicine candidate gate v4

The first live P5 transcript was:
> No, no medicine as of now. I just have some pain on my palm, that's all.

Raw LLM message content (the validated value was also empty):
```json
{"medicines":{"value":[],"status":"ok","evidence":"No, no medicine as of now"}}
```

Old transcript-scanning fuzzy output, replayed using the unchanged v3 implementation:
```json
[{"name":"Pan","strength":null,"purpose":null,"display":"Pan","match_score":85.71,"status":"needs_confirmation"}]
```

The old UI ignored the empty extracted list and discovered a fuzzy medicine independently in the transcript. This was a deterministic matching/orchestration error, not an STT or LLM error. The second recording correctly yielded an empty list in both paths.

## Rules

- Match only validated LLM medicine candidates against the unchanged vocabulary. Without candidates, matching fails closed.
- Require transcript grounding; symptom/anatomy words cannot be names or matched spans.
- Brands of at most four characters require exact tokens and nearby medicine-taking context or an adjacent strength. Taking/drinking context is supported in English, Hindi and Hinglish.
- Explicit medication denial yields an accepted empty list unless a supported positive medicine remains. Scope negation around contrasts/corrections; denied purpose-only medicines are not added.
- Unknown medicine names can retain a transcript-supported purpose; common condition names and abbreviations are equivalent.
- Confirm a complete vocabulary base in an extracted multiword identity, including identities with a descriptive suffix. Never discover unrelated vocabulary names by scanning free words.
- Rejected nonempty lists without explicit denial remain unclear rather than becoming a negative assertion. Strength is not invented from the vocabulary.
- No prompt, vocabulary, ground truth or scoring-rule changes. A later explicit medicine correction still requires a new P5 recording/read-back in the app.

## Offline comparison

All Set B summary metrics are identical to v3. Replayed all 212 cached clips / 20 sessions. Saved per-clip, per-session, summary and comparison CSVs with `_v4` suffixes.

| Set B metric | ch v3 → v4 | tm v3 → v4 | Overall v3 → v4 |
|---|---|---|---|
| Medicine names, sessions | 9/10 → 9/10 | 8/10 → 8/10 | 17/20 → 17/20 |
| Medicine names + strengths, sessions | 9/10 → 9/10 | 8/10 → 8/10 | 17/20 → 17/20 |
| Individual medicine names | 15/16 → 15/16 | 14/16 → 14/16 | 29/32 → 29/32 |
| Individual strengths | 6/7 → 6/7 | 5/7 → 5/7 | 11/14 → 11/14 |
| Complete records | 6/10 → 6/10 | 2/10 → 2/10 | 8/20 → 8/20 |
| Red flags caught | 2/2 → 2/2 | 2/2 → 2/2 | 4/4 → 4/4 |
| False alarms | 0/8 → 0/8 | 1/8 → 1/8 | 1/16 → 1/16 |

Set A has only raw STT evaluation, no separate v3 generation or cached LLM extractions. Its original frozen scores are used as the v3-era baseline, explicitly labelled in the comparison file. Only ch transcripts were processed. This confirms raw STT scoring is unchanged; it does **not** measure the LLM candidate gate on Set A.

| Set A ch metric | Baseline | v4 |
|---|---|---|
| Names, keyterms off | 16/29 | 16/29 |
| Names, keyterms on | 28/29 | 28/29 |
| Names + strength, keyterms off | 7/11 | 7/11 |
| Names + strength, keyterms on | 9/11 | 9/11 |

Network/provider functions were blocked during replay. **0 Prisma, 0 Groq, 0 Timbre calls.** Historical outputs are hash-verified unchanged in `medicines_audit_v4.json`. Initial implementation replay artifacts are retained separately in ignored `cache/medicine_guard_initial_replay`; they are not the final v4 results.

103 Python tests pass, including the five requested examples and the simulated live read-back regression. Existing matcher tests now supply explicit candidate fixtures and reject context-free short names.
