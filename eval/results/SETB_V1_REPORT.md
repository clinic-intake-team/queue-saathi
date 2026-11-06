# Official full Set B v1 — completed

All 212 clips and 20 sessions completed with openai/gpt-oss-120b and original medium reasoning. No scoring/prompt/keyterm changes were made after results were observed. Existing exploratory and Set C comparison files remain separate.

| Metric | Overall | ch | tm |
|---|---|---|---|
| Token | 19/20 | 10/10 | 9/10 |
| Age | 18/20 | 9/10 | 9/10 |
| Sex | 19/20 | 9/10 | 10/10 |
| Complaint | 12/20 | 7/10 | 5/10 |
| Duration | 16/20 | 9/10 | 7/10 |
| Follow-ups | 15/20 | 9/10 | 6/10 |
| Allergies | 16/20 | 7/10 | 9/10 |
| Conditions | 19/20 | 9/10 | 10/10 |
| Medicine names + strengths (all medicines in session) | 17/20 | 9/10 | 8/10 |
| Medicine names (per medicine) | 29/32 | 15/16 | 14/16 |
| Name + strength (strength-bearing medicines) | 11/14 | 6/7 | 5/7 |
| Red flags caught | 4/4 | 2/2 | 2/2 |
| False alarms | 11/16 | 4/8 | 7/8 |
| Complete records | 2/20 | 1/10 | 1/10 |
| Clips with invalid LLM fields | 20/212 | 9/106 | 11/106 |

API attempts across the official run: 212 Prisma and 171 Groq. The final resume made 102 Groq attempts and 0 Prisma attempts, reusing 110 completed/cached extractions and all 212 STT responses. Across the full logical 212-clip run, 41 extraction requests were satisfied by identical-request caching. No HTTP 429 occurred in the final resume.

The fail-safe caught all 4 positive sessions but also alerted on 11/16 negatives. Complete-record accuracy was 2/20 under the frozen rubric; name+strength accuracy across all medicines within a session was 17/20. Do not conflate these denominators with per-medicine 29/32 names and 11/14 strength-bearing name+strength counts.

All per-field metrics, silently_wrong, safe_miss and invalid-output counts are in setB_summary.csv. All 20 sessions have complete ground-truth coverage, including user-supplied S02 location alternatives and pain score.

Every failed field for both speakers, with transcript, expected/got and the frozen automated cause label, is in setB_failures_v1.txt. Those cause labels are provisional transcript-based diagnostics, not a confirmed audio audit; strict paraphrase/relative-time scoring can require human review. They were not used to change scores or tune rules.

Saved outputs: setB_per_clip.csv, setB_per_session.csv, setB_summary.csv, setB_failures_v1.txt, setB_run_audit_v1.json. Existing v1 result files are protected from overwrite. Any later changes require separately saved v2 results.
