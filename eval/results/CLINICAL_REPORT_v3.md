# Clinical v3 regression

Baseline: final v2 Part B. No Prisma, Groq or Timbre calls during this re-score.

| Set | Metric | v2 | v3 |
|---|---|---|---|
| B | complaint | 14/20 | 14/20 |
| B | duration_days | 18/20 | 18/20 |
| B | red_flags_caught | 4/4 | 4/4 |
| B | false_alarms | 1/16 | 1/16 |
| B | complete_record | 8/20 | 8/20 |
| C symptom_keyterms_off | status | 23/24 | 23/24 |
| C symptom_keyterms_off | value | 21/24 | 21/24 |
| C symptom_keyterms_off | red_flags_caught | 4/4 | 4/4 |
| C symptom_keyterms_off | false_alarms | 0/2 | 0/2 |
| C symptom_keyterms_on | status | 23/24 | 23/24 |
| C symptom_keyterms_on | value | 22/24 | 22/24 |
| C symptom_keyterms_on | red_flags_caught | 4/4 | 4/4 |
| C symptom_keyterms_on | false_alarms | 0/2 | 0/2 |

No new alert rows on any question. Set B false alarms: ch 0/8, tm 1/8 (unchanged). Set C false alarms: ch 0/1, tm 0/1 in both conditions (unchanged).

All v2 output files and ground truth were hash-verified unchanged. This regression does not measure sensitivity to newly added symptom categories: those categories are covered by new synthetic unit tests, not new patient recordings.

P7 now asks about TB, heart disease and epilepsy. The conditions schema accepts canonical labels `TB`, `heart disease`, `epilepsy`; invalid or unsupported values still fail field validation.

New rules were fixed before reading the re-score outcomes; no post-result vocabulary or scoring adjustment was made.
