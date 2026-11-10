# Part A v2 — cached code-only comparison

No Prisma or Groq calls. Original v1 code/results/data/prompt files were hash-verified unchanged. The explicitly requested SCORING_NOTES.md amendment preserves its original text, with exact original bytes in SCORING_NOTES_v1.md. v2 implementation lives in separate modules.

## Set B

All cells are v1 → v2.

| Metric | Overall | ch | tm |
|---|---|---|---|
| Token | 19/20 → 19/20 | 10/10 → 10/10 | 9/10 → 9/10 |
| Age | 18/20 → 18/20 | 9/10 → 9/10 | 9/10 → 9/10 |
| Sex | 19/20 → 19/20 | 9/10 → 9/10 | 10/10 → 10/10 |
| Complaint | 12/20 → 13/20 | 7/10 → 8/10 | 5/10 → 5/10 |
| Duration | 16/20 → 16/20 | 9/10 → 9/10 | 7/10 → 7/10 |
| Follow-ups | 15/20 → 16/20 | 9/10 → 10/10 | 6/10 → 6/10 |
| Medicine names + required strengths per session | 17/20 → 17/20 | 9/10 → 9/10 | 8/10 → 8/10 |
| Allergies | 16/20 → 18/20 | 7/10 → 9/10 | 9/10 → 9/10 |
| Conditions | 19/20 → 19/20 | 9/10 → 9/10 | 10/10 → 10/10 |
| Red flags caught | 4/4 → 4/4 | 2/2 → 2/2 | 2/2 → 2/2 |
| False alarms | 11/16 → 1/16 | 4/8 → 0/8 | 7/8 → 1/8 |
| Complete records | 2/20 → 7/20 | 1/10 → 5/10 | 1/10 → 2/10 |
| Clips with invalid fields | 20/212 → 2/212 | 9/106 → 0/106 | 11/106 → 2/106 |

Remaining B false alarm: tm S02, P4, unintelligible transcript; P4 needs_check remains an alert by requirement. Remaining invalid B clips: tm S04 F1 (follow_up inner schema) and tm S06 P2 (complaint evidence not verbatim). No new prompt or evidence-repair calls were used to address them.

## Set C

Baseline is the latest medium-effort development run 2 in the untagged v1 comparison CSVs, not the low-effort experiment or the older 24-row historical snapshot.

| Keyterms | Speaker | Status | Value | Red flags caught | False alarms | Invalid-field clips |
|---|---|---|---|---|---|---|
| off | overall | 22/24 → 23/24 | 21/24 → 21/24 | 4/4 → 4/4 | 0/2 → 0/2 | 1 → 0 |
| off | ch | 12/12 → 12/12 | 12/12 → 12/12 | 2/2 → 2/2 | 0/1 → 0/1 | 0 → 0 |
| off | tm | 10/12 → 11/12 | 9/12 → 9/12 | 2/2 → 2/2 | 0/1 → 0/1 | 1 → 0 |
| on | overall | 23/24 → 23/24 | 22/24 → 22/24 | 4/4 → 4/4 | 0/2 → 0/2 | 0 → 0 |
| on | ch | 12/12 → 12/12 | 11/12 → 11/12 | 2/2 → 2/2 | 0/1 → 0/1 | 0 → 0 |
| on | tm | 11/12 → 11/12 | 11/12 → 11/12 | 2/2 → 2/2 | 0/1 → 0/1 | 0 → 0 |

Set C keyterms-off silently_wrong changes 1→2 and safe_miss 2→1. The existing tm C09 empty safety list becomes valid under the new empty-list evidence policy but still lacks the expected extracted symptom; the independent blood keyword continues to alert. Value accuracy remains 21/24. Keyterms-on silently_wrong=1 and safe_miss=1 remain unchanged, with value accuracy 22/24. No P4 denial from one C clip is borrowed for another clip.

## Verification and gate

57 offline tests passed. Provider/network entry points were blocked for the re-score. Set B used 212 original response payloads; Set C used 23 original response payload rows plus 25 original parsed-generation cache rows. Earlier implementation candidates are archived separately and are not the final v2 result. All scoring/parser changes are documented in eval/SCORING_NOTES.md.

STOP after Part A. Part B visit_reason/duration prompt changes and one-call evidence repair have not been implemented or run. Build and show a cache-aware Part B call-count gate only after this confirmation gate.
