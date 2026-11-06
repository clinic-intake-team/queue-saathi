# Set C: frozen run 2 versus reasoning_effort=low

Only Set C scores are reported. Partial Set B scores and per-clip outputs remain hidden.

Model: openai/gpt-oss-120b. Frozen run-2 extraction prompt, validator, red-flag rules and scoring were loaded from verified Git blobs matching eval/setC_development_v2_protocol.json. No prompt or scoring changes were made after this comparison. Prisma responses were read directly from cache; no Prisma calls occurred.

## Status, value and invalid-field comparison

Each pair is run 2 → low.

| Condition | Speaker | Status | Value | Invalid-field clips |
|---|---|---|---|---|
| symptom_keyterms_off | overall | 22/24 → 18/24 | 21/24 → 13/24 | 1 → 6 |
| symptom_keyterms_off | ch | 12/12 → 10/12 | 12/12 → 8/12 | 0 → 2 |
| symptom_keyterms_off | tm | 10/12 → 8/12 | 9/12 → 5/12 | 1 → 4 |
| symptom_keyterms_on | overall | 23/24 → 19/24 | 22/24 → 15/24 | 0 → 5 |
| symptom_keyterms_on | ch | 12/12 → 10/12 | 11/12 → 8/12 | 0 → 2 |
| symptom_keyterms_on | tm | 11/12 → 9/12 | 11/12 → 7/12 | 0 → 3 |

## Safety and error metrics

| Condition | Speaker | Red flags caught | False alarms | Silently wrong | Safe miss |
|---|---|---|---|---|---|
| symptom_keyterms_off | overall | 4/4 → 4/4 | 0/2 → 2/2 | 1 → 6 | 2 → 5 |
| symptom_keyterms_off | ch | 2/2 → 2/2 | 0/1 → 1/1 | 0 → 3 | 0 → 1 |
| symptom_keyterms_off | tm | 2/2 → 2/2 | 0/1 → 1/1 | 1 → 3 | 2 → 4 |
| symptom_keyterms_on | overall | 4/4 → 4/4 | 0/2 → 2/2 | 1 → 5 | 1 → 4 |
| symptom_keyterms_on | ch | 2/2 → 2/2 | 0/1 → 1/1 | 1 → 3 | 0 → 1 |
| symptom_keyterms_on | tm | 2/2 → 2/2 | 0/1 → 1/1 | 0 → 2 | 1 → 3 |

## Usage and decision

This comparison made 28 successful Groq calls, 0 Prisma calls, and used 25,367 total tokens (905.96 per call).

At stop, Set B averaged 1,500.22 tokens per successful call (69 calls, 103,515 tokens). Projecting that average to 212 calls gives 318,046 tokens, 59.0% over the published 200,000/day default. Across all 124 successful calls logged at the stop, the average was 1,325.07 and the 212-call projection was 280,915. These total-token projections do not establish exact remaining quota or account for provider-side cached-token exemptions.

The low-effort Set C average is not directly transferable to Set B: this comparison intentionally used the shorter frozen run-2 prompt, whereas Set B uses the expanded all-row prompt. Its naive same-cost 212-call projection is not a new Set B gate estimate.

Low reasoning effort did NOT retain run-2 quality. STOP: no Set B LLM results discarded, no Prisma caches deleted, no Set B restart, and no new official-v1 run authorized through this experiment. LLM_REASONING_EFFORT remains set to low as requested; the frozen old Set B protocol prevents accidental use of modified code.
