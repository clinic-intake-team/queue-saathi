# Evaluation results

All recordings are scripted by two team members, not real patients. Versioned outputs are preserved so improvements can be inspected rather than replacing the original baseline.

| Dataset | Scope | How to interpret it |
|---|---|---|
| **Set A** | 40 medicine-name clips; two speakers | `setA_summary.csv`: Prisma keyterms off vs on, 30/58 → 55/58 medicine mentions (52% → 95%). Strength accuracy is a separate metric. `*_v4` is a later medicine-parser regression on the ch development speaker only; it is not a replacement two-speaker STT experiment. |
| **Set B v1** | 212 recordings covering 20 full scripted sessions | Original official held-out run, saved in untagged `setB_*` files and `SETB_V1_REPORT.md`. Count a full session once rather than treating its recordings as independent patients. |
| **Set B v2 onward** | Same recordings after inspecting v1 failures | Development results after validation/safety fixes (`*_v2`) and later P2/P3 prompt changes (`*_partB_v2`). `*_v3` adds clinical keyword checks; `*_v4` checks the medicine parser. These are not fresh held-out results. |
| **Set C** | 24 independent edge-case clips, 12 per speaker | Development set for extraction, validation and safety. Keyterms-off/on experiments can produce 48 rows from 24 unique clips. Independent clips must not be treated as complete linked sessions. |

## Finding the current numbers

- **Medicine-name STT comparison:** `setA_summary.csv` (40 unique recordings).
- **Current full-session development summary:** `setB_summary_v4.csv` (4/4 positive sessions flagged; 1/16 false alarms).
- **Safety-fix comparison:** `PART_A_REPORT_v2.md` (11/16 → 1/16 false alarms).
- **Current Set C keyword regression:** `setC_summary_v3.csv`.
- **Scoring rules and changes:** `../SCORING_NOTES.md`, the named historical notes and protocols.

`per_clip` files contain transcripts, extracted fields and scores; `per_session` files aggregate full sessions; `summary` and `comparison` files supply the reported metrics. Intermediate candidates and the low-reasoning experiment remain in named subdirectories and are not the official v1 result. Audit JSONs record provenance and cache reuse. Inventories and protocol inputs remain under `eval/` because runners reference those fixed paths.

All 276 unique clips were used during project development. The reported metrics have different denominators and are not whole-record accuracy, a clinical trial, or a safety guarantee. Source audio, patient-session stores, provider caches and logs are intentionally excluded from Git. Cached re-scoring needs the author's local caches; a fresh clone can inspect the published outputs and run unit tests without them.
