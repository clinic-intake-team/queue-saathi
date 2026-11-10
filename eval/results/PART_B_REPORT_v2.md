# Part B v2 — three-way comparison

Completed: 64 P2/P3 row entries, 54 unique primary Groq calls, 10 duplicate row entries served from the new cache, 0 evidence-repair calls, 0 Prisma calls. No daily quota response occurred. All other B/C rows reused Part A outputs. Model openai/gpt-oss-120b, medium reasoning.

## Set B

| Speaker | Metric | v1 | v2 Part A | v2 Part B |
|---|---|---|---|---|
| overall | token | 19/20 | 19/20 | 19/20 |
| overall | age | 18/20 | 18/20 | 18/20 |
| overall | sex | 19/20 | 19/20 | 19/20 |
| overall | allergies | 16/20 | 18/20 | 18/20 |
| overall | conditions | 19/20 | 19/20 | 19/20 |
| overall | complaint | 12/20 | 13/20 | 14/20 |
| overall | duration_days | 16/20 | 16/20 | 18/20 |
| overall | followups | 15/20 | 16/20 | 16/20 |
| overall | medicines_names_strengths | 17/20 | 17/20 | 17/20 |
| overall | visit_reason | n.a. | n.a. | 18/20 |
| overall | red_flags_caught | 4/4 | 4/4 | 4/4 |
| overall | false_alarms | 11/16 | 1/16 | 1/16 |
| overall | complete_record | 2/20 | 7/20 | 8/20 |
| overall | invalid_llm_output | 20/212 | 2/212 | 1/212 |
| ch | token | 10/10 | 10/10 | 10/10 |
| ch | age | 9/10 | 9/10 | 9/10 |
| ch | sex | 9/10 | 9/10 | 9/10 |
| ch | allergies | 7/10 | 9/10 | 9/10 |
| ch | conditions | 9/10 | 9/10 | 9/10 |
| ch | complaint | 7/10 | 8/10 | 8/10 |
| ch | duration_days | 9/10 | 9/10 | 10/10 |
| ch | followups | 9/10 | 10/10 | 10/10 |
| ch | medicines_names_strengths | 9/10 | 9/10 | 9/10 |
| ch | visit_reason | n.a. | n.a. | 9/10 |
| ch | red_flags_caught | 2/2 | 2/2 | 2/2 |
| ch | false_alarms | 4/8 | 0/8 | 0/8 |
| ch | complete_record | 1/10 | 5/10 | 6/10 |
| ch | invalid_llm_output | 9/106 | 0/106 | 0/106 |
| tm | token | 9/10 | 9/10 | 9/10 |
| tm | age | 9/10 | 9/10 | 9/10 |
| tm | sex | 10/10 | 10/10 | 10/10 |
| tm | allergies | 9/10 | 9/10 | 9/10 |
| tm | conditions | 10/10 | 10/10 | 10/10 |
| tm | complaint | 5/10 | 5/10 | 6/10 |
| tm | duration_days | 7/10 | 7/10 | 8/10 |
| tm | followups | 6/10 | 6/10 | 6/10 |
| tm | medicines_names_strengths | 8/10 | 8/10 | 8/10 |
| tm | visit_reason | n.a. | n.a. | 9/10 |
| tm | red_flags_caught | 2/2 | 2/2 | 2/2 |
| tm | false_alarms | 7/8 | 1/8 | 1/8 |
| tm | complete_record | 1/10 | 2/10 | 2/10 |
| tm | invalid_llm_output | 11/106 | 2/106 | 1/106 |

## Set C

The v1 comparison baseline is the latest medium-effort run-2 summary; earlier historical and low-effort results are unchanged.

| Keyterms | Speaker | Metric | v1 | v2 Part A | v2 Part B |
|---|---|---|---|---|---|
| off | overall | status | 22/24 | 23/24 | 23/24 |
| off | overall | value | 21/24 | 21/24 | 21/24 |
| off | overall | red_flags_caught | 4/4 | 4/4 | 4/4 |
| off | overall | false_alarms | 0/2 | 0/2 | 0/2 |
| off | overall | silently_wrong | 1 | 2 | 2 |
| off | overall | safe_miss | 2 | 1 | 1 |
| off | overall | needs_check | 1 | 0 | 0 |
| off | overall | clips_with_invalid_fields | 1 | 0 | 0 |
| off | ch | status | 12/12 | 12/12 | 12/12 |
| off | ch | value | 12/12 | 12/12 | 12/12 |
| off | ch | red_flags_caught | 2/2 | 2/2 | 2/2 |
| off | ch | false_alarms | 0/1 | 0/1 | 0/1 |
| off | ch | silently_wrong | 0 | 0 | 0 |
| off | ch | safe_miss | 0 | 0 | 0 |
| off | ch | needs_check | 0 | 0 | 0 |
| off | ch | clips_with_invalid_fields | 0 | 0 | 0 |
| off | tm | status | 10/12 | 11/12 | 11/12 |
| off | tm | value | 9/12 | 9/12 | 9/12 |
| off | tm | red_flags_caught | 2/2 | 2/2 | 2/2 |
| off | tm | false_alarms | 0/1 | 0/1 | 0/1 |
| off | tm | silently_wrong | 1 | 2 | 2 |
| off | tm | safe_miss | 2 | 1 | 1 |
| off | tm | needs_check | 1 | 0 | 0 |
| off | tm | clips_with_invalid_fields | 1 | 0 | 0 |
| on | overall | status | 23/24 | 23/24 | 23/24 |
| on | overall | value | 22/24 | 22/24 | 22/24 |
| on | overall | red_flags_caught | 4/4 | 4/4 | 4/4 |
| on | overall | false_alarms | 0/2 | 0/2 | 0/2 |
| on | overall | silently_wrong | 1 | 1 | 1 |
| on | overall | safe_miss | 1 | 1 | 1 |
| on | overall | needs_check | 0 | 0 | 0 |
| on | overall | clips_with_invalid_fields | 0 | 0 | 0 |
| on | ch | status | 12/12 | 12/12 | 12/12 |
| on | ch | value | 11/12 | 11/12 | 11/12 |
| on | ch | red_flags_caught | 2/2 | 2/2 | 2/2 |
| on | ch | false_alarms | 0/1 | 0/1 | 0/1 |
| on | ch | silently_wrong | 1 | 1 | 1 |
| on | ch | safe_miss | 0 | 0 | 0 |
| on | ch | needs_check | 0 | 0 | 0 |
| on | ch | clips_with_invalid_fields | 0 | 0 | 0 |
| on | tm | status | 11/12 | 11/12 | 11/12 |
| on | tm | value | 11/12 | 11/12 | 11/12 |
| on | tm | red_flags_caught | 2/2 | 2/2 | 2/2 |
| on | tm | false_alarms | 0/1 | 0/1 | 0/1 |
| on | tm | silently_wrong | 0 | 0 | 0 |
| on | tm | safe_miss | 1 | 1 | 1 |
| on | tm | needs_check | 0 | 0 | 0 |
| on | tm | clips_with_invalid_fields | 0 | 0 | 0 |

## Interpretation and preservation

Set B gains relative to Part A: complaint 13/20→14/20, duration 16/20→18/20, complete records 7/20→8/20, invalid-field clips 2/212→1/212. Both same-day S03 durations now return 0. Complaint gains occurred for tm S02 and tm S05, with one regression at tm S03: the new summary says pressing sensation, which the unchanged heaviness matcher does not accept. No post-result synonym or scoring adjustment was made.

Set C aggregate results are unchanged from Part A. All four expected positive clips still alert with no false alarms in either keyterm condition. The Part A keyterms-off trade-off (silently_wrong=2, safe_miss=1) remains; evidence/schema normalization does not prove clinical correctness.

visit_reason is supplemental (18/20), with no baseline field score. Its explicit check-up purposes feed the already-required complaint reason concepts. duration_hours is recorded when supported but unscored because no hours truth was supplied. Existing complete-record criteria remain comparable. The remaining B invalid clip is an unchanged follow-up schema issue, outside this run's P2/P3 re-extraction scope.

V1 and Part A data/code/scoring inputs were hash-verified unchanged. Original scoring-note text and the Part A note version are separately preserved. New outputs end in _partB_v2.csv. Generation and response caches were preserved throughout. Two CSV-deserialization reporting issues were fixed offline after all generations completed; the finalizer reconstructs the exact pre-fix runner hash and checks all other generation/scoring hashes. No extra API calls were needed and no grading rule changed.

Evidence-only repair is implemented for every supported row in the shared v2 app extraction entry point and unit-tested for success, failure, immutable values and quota-resume behavior. No repair was needed by this live P2/P3 run. The v2 Streamlit UI remains the existing Phase 1 shell; this work does not claim a completed patient conversation UI.
