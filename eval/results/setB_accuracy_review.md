# Set B accuracy review (exploratory)

This is a post-run manual review of the 50 structured P1–P5 rows in `setB_per_recording.csv`, compared with the S01–S10 facts in `test-scripts.md`. It is exploratory, not a pre-registered/frozen Set B scoring protocol. P0, P6, P7, follow-ups, and R1 are transcript-only in the current evaluator and are not included.

## Question-level results

| Question | Review counts |
|---|---|
| P1 | 9 correct, 1 incorrect |
| P2 | 1 incorrect, 3 partial, 5 correct, 1 unclear |
| P3 | 1 incorrect, 7 correct, 2 unclear |
| P4 | 7 exact matches; 3 needs-check outcomes (2 expected positives caught; 3 negative sessions routed to review) |
| P5 | 8 correct, 1 partial, 1 incorrect |

## Main findings

- P1 age: 9/10 exact. S03 audio says 62, but Gnani transcript says 52; Groq follows the transcript.
- P2: replay confirmed S01 says fever, but the transcript omits it (STT miss). S02 extraction omits the BP-check reason; S05 drops the one-time vomiting detail; S06 drops the sugar-check reason. For S09, user replay confirms “left hand,” but the symptom wording (card: weakness) remains unresolved; retain as unclear.
- P3: S01 is a confirmed STT miss: user replay says “teen din ho gaye” (3 days), but transcript is blank. S03 (“since this morning”) needs a rule for relative-time normalization. User confirmed S09 says “since evening,” while the card says one day; retain as a recording/card mismatch.
- P4: both expected positives (S03, S09) alert. S02 is a confirmed STT miss: user replay says “nahi, aisa nahi hai,” but the transcript was garbled, causing a safe `needs_check`. S04 and S10 say “no” but are classified as `declined`, also routing to `needs_check`.
- P5: S02 is a confirmed STT miss: audio says Telma 40, transcript says Telma H; Amlong 5 is correct. S03 is a confirmed STT mismatch: audio says Ecosprin 75 and Atorva (slight pronunciation variation), while transcript says Aspirin and Sandify and omits 75; Atorva is correct. Other expected medicine names were captured in this exploratory review.

## Interpretation

The CSV has 106 rows, zero run errors, zero extraction validation errors, and 50 structured extractions. These processing counts do not mean all answers are accurate. P2 completeness, P3 relative-time normalization, medicine alias policy, and whether a `needs_check` counts as a false alarm should be formally defined before publishing a single aggregate score.
