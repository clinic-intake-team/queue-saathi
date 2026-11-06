# Set B Stage 1 — proposed mapping (NOT copied)

This is a filename/metadata/duration inventory only. No Set B audio was listened to or transcribed, no speaking lines/ground truth read, and no API calls made. All originals remain in place. STOP before copying.

## Naming and inference

- ch: raw/setB_chill/Sxx/B_Sn_ROW_chill.m4a, with mixed zero padding and Chill/chill capitalization.
- tm: raw/setB_tm/Sxx/B_Sxx_ROW.m4a.
- P0–P7/R1 and numbered follow-ups map directly; session numbers are padded to two digits.
- Semantic follow-up proposals: F(measured)→F1, F(chills)→F2; F(where)→F1, F(pain)→F2; F(last BP)→F3; F(phlegm)→F1, F(breathless)→F2; F(how)/F(last)→F1. These are filename-based inferences requiring confirmation, not verified audio content.
- No files are unnamed; creation-time fallback was not used. Creation timestamps and SHA-256 hashes are included in the CSV for audit.
- ch S02: two different P2-labelled files collide; P3 is missing. Neither is silently reassigned.
- ch S07: named F3 is unexpected and F2 is missing. F3→F2 is a suggestion only, not an approved mapping.

## Counts

| Speaker | Session | Expected | Found | Missing | Extra | Duplicated row | ≥30 s |
|---|---|---:|---:|---|---|---|---:|
| ch | S01 | 11 | 11 | — | — | — | 0 |
| ch | S02 | 12 | 12 | P3 | — | P2 ×2 | 0 |
| ch | S03 | 11 | 11 | — | — | — | 0 |
| ch | S04 | 11 | 11 | — | — | — | 0 |
| ch | S05 | 10 | 10 | — | — | — | 0 |
| ch | S06 | 10 | 10 | — | — | — | 0 |
| ch | S07 | 11 | 11 | F2 | F3 (1) | — | 0 |
| ch | S08 | 11 | 11 | — | — | — | 0 |
| ch | S09 | 9 | 9 | — | — | — | 0 |
| ch | S10 | 10 | 10 | — | — | — | 0 |
| tm | S01 | 11 | 11 | — | — | — | 0 |
| tm | S02 | 12 | 12 | — | — | — | 0 |
| tm | S03 | 11 | 11 | — | — | — | 0 |
| tm | S04 | 11 | 11 | — | — | — | 0 |
| tm | S05 | 10 | 10 | — | — | — | 0 |
| tm | S06 | 10 | 10 | — | — | — | 0 |
| tm | S07 | 11 | 11 | — | — | — | 0 |
| tm | S08 | 11 | 11 | — | — | — | 0 |
| tm | S09 | 9 | 9 | — | — | — | 0 |
| tm | S10 | 10 | 10 | — | — | — | 0 |

## Full mapping and durations

Duplicate destination entries are conflicts, not instructions to overwrite. A blank destination is deliberately unresolved.

| Source | Proposed destination | Duration (s) | Status / notes |
|---|---|---:|---|
| `raw/setB_chill/S01/B_S1_P0_chill.m4a` | `recordings/ch_S01_P0.m4a` | 2.901 | direct;  |
| `raw/setB_chill/S01/B_S1_P1_chill.m4a` | `recordings/ch_S01_P1.m4a` | 2.987 | direct;  |
| `raw/setB_chill/S01/B_S1_P2_chill.m4a` | `recordings/ch_S01_P2.m4a` | 4.949 | direct;  |
| `raw/setB_chill/S01/B_S1_P3_chill.m4a` | `recordings/ch_S01_P3.m4a` | 2.731 | direct;  |
| `raw/setB_chill/S01/B_S1_F1_chill.m4a` | `recordings/ch_S01_F1.m4a` | 4.779 | direct;  |
| `raw/setB_chill/S01/B_S1_F2_chill.m4a` | `recordings/ch_S01_F2.m4a` | 3.755 | direct;  |
| `raw/setB_chill/S01/B_S1_P4_chill.m4a` | `recordings/ch_S01_P4.m4a` | 2.816 | direct;  |
| `raw/setB_chill/S01/B_S1_P5_chill.m4a` | `recordings/ch_S01_P5.m4a` | 3.669 | direct;  |
| `raw/setB_chill/S01/B_S1_R1_chill.m4a` | `recordings/ch_S01_R1.m4a` | 2.901 | direct;  |
| `raw/setB_chill/S01/B_S1_P6_chill.m4a` | `recordings/ch_S01_P6.m4a` | 3.072 | direct;  |
| `raw/setB_chill/S01/B_S1_P7_chill.m4a` | `recordings/ch_S01_P7.m4a` | 3.755 | direct;  |
| `raw/setB_chill/S02/B_S2_P0_chill.m4a` | `recordings/ch_S02_P0.m4a` | 3.157 | direct;  |
| `raw/setB_chill/S02/B_S2_P1_chill.m4a` | `recordings/ch_S02_P1.m4a` | 3.755 | direct;  |
| `raw/setB_chill/S02/B_S2_P2_chill 2.m4a` | `recordings/ch_S02_P2.m4a` | 4.523 | duplicate_destination_do_not_copy;  Two distinct P2-labelled files; P3 is missing. Confirm which file is P3, or supply it. |
| `raw/setB_chill/S02/B_S2_P2_chill.m4a` | `recordings/ch_S02_P2.m4a` | 6.315 | duplicate_destination_do_not_copy;  Two distinct P2-labelled files; P3 is missing. Confirm which file is P3, or supply it. |
| `raw/setB_chill/S02/B_S2_F1_chill.m4a` | `recordings/ch_S02_F1.m4a` | 6.741 | direct;  |
| `raw/setB_chill/S02/B_S2_F2_chill.m4a` | `recordings/ch_S02_F2.m4a` | 3.925 | direct;  |
| `raw/setB_chill/S02/B_S2_F3_chill.m4a` | `recordings/ch_S02_F3.m4a` | 3.669 | direct;  |
| `raw/setB_chill/S02/B_S2_P4_chill.m4a` | `recordings/ch_S02_P4.m4a` | 3.328 | direct;  |
| `raw/setB_chill/S02/B_S2_P5_chill.m4a` | `recordings/ch_S02_P5.m4a` | 5.888 | direct;  |
| `raw/setB_chill/S02/B_S2_R1_chill.m4a` | `recordings/ch_S02_R1.m4a` | 4.523 | direct;  |
| `raw/setB_chill/S02/B_S2_P6_chill.m4a` | `recordings/ch_S02_P6.m4a` | 3.243 | direct;  |
| `raw/setB_chill/S02/B_S2_P7_chill.m4a` | `recordings/ch_S02_P7.m4a` | 4.608 | direct;  |
| `raw/setB_chill/S03/B_S03_P0_Chill.m4a` | `recordings/ch_S03_P0.m4a` | 1.556 | direct;  |
| `raw/setB_chill/S03/B_S03_P1_Chill.m4a` | `recordings/ch_S03_P1.m4a` | 4.265 | direct;  |
| `raw/setB_chill/S03/B_S03_P2_Chill.m4a` | `recordings/ch_S03_P2.m4a` | 5.887 | direct;  |
| `raw/setB_chill/S03/B_S03_P3_Chill.m4a` | `recordings/ch_S03_P3.m4a` | 2.196 | direct;  |
| `raw/setB_chill/S03/B_S03_F(where)_Chill.m4a` | `recordings/ch_S03_F1.m4a` | 5.353 | inferred_from_label_confirm;  |
| `raw/setB_chill/S03/B_S03_F(pain)_Chill.m4a` | `recordings/ch_S03_F2.m4a` | 2.836 | inferred_from_label_confirm;  |
| `raw/setB_chill/S03/B_S03_P4_Chill.m4a` | `recordings/ch_S03_P4.m4a` | 5.887 | direct;  |
| `raw/setB_chill/S03/B_S03_P5_Chill.m4a` | `recordings/ch_S03_P5.m4a` | 5.055 | direct;  |
| `raw/setB_chill/S03/B_S03_R1_Chill.m4a` | `recordings/ch_S03_R1.m4a` | 1.748 | direct;  |
| `raw/setB_chill/S03/B_S03_P6_Chill.m4a` | `recordings/ch_S03_P6.m4a` | 1.620 | direct;  |
| `raw/setB_chill/S03/B_S03_P7_Chill.m4a` | `recordings/ch_S03_P7.m4a` | 3.903 | direct;  |
| `raw/setB_chill/S04/B_S04_P0_Chill.m4a` | `recordings/ch_S04_P0.m4a` | 1.705 | direct;  |
| `raw/setB_chill/S04/B_S04_P1_Chill.m4a` | `recordings/ch_S04_P1.m4a` | 2.473 | direct;  |
| `raw/setB_chill/S04/B_S04_P2_Chill.m4a` | `recordings/ch_S04_P2.m4a` | 4.777 | direct;  |
| `raw/setB_chill/S04/B_S04_P3_Chill.m4a` | `recordings/ch_S04_P3.m4a` | 3.519 | direct;  |
| `raw/setB_chill/S04/B_S04_F(phlegm)_Chill.m4a` | `recordings/ch_S04_F1.m4a` | 3.540 | inferred_from_label_confirm;  |
| `raw/setB_chill/S04/B_S04_F(breathless)_Chill.m4a` | `recordings/ch_S04_F2.m4a` | 2.772 | inferred_from_label_confirm;  |
| `raw/setB_chill/S04/B_S04_P4_Chill.m4a` | `recordings/ch_S04_P4.m4a` | 3.241 | direct;  |
| `raw/setB_chill/S04/B_S04_P5_Chill.m4a` | `recordings/ch_S04_P5.m4a` | 3.711 | direct;  |
| `raw/setB_chill/S04/B_S04_R1_Chill.m4a` | `recordings/ch_S04_R1.m4a` | 1.577 | direct;  |
| `raw/setB_chill/S04/B_S04_P6_Chill.m4a` | `recordings/ch_S04_P6.m4a` | 5.268 | direct;  |
| `raw/setB_chill/S04/B_S04_P7_Chill.m4a` | `recordings/ch_S04_P7.m4a` | 3.391 | direct;  |
| `raw/setB_chill/S05/B_S5_P0_chill.m4a` | `recordings/ch_S05_P0.m4a` | 2.901 | direct;  |
| `raw/setB_chill/S05/B_S5_P1_chill.m4a` | `recordings/ch_S05_P1.m4a` | 4.267 | direct;  |
| `raw/setB_chill/S05/B_S5_P2_chill.m4a` | `recordings/ch_S05_P2.m4a` | 6.059 | direct;  |
| `raw/setB_chill/S05/B_S5_P3_chill.m4a` | `recordings/ch_S05_P3.m4a` | 2.645 | direct;  |
| `raw/setB_chill/S05/B_S5_F1_chill.m4a` | `recordings/ch_S05_F1.m4a` | 3.584 | direct;  |
| `raw/setB_chill/S05/B_S5_P4_chill.m4a` | `recordings/ch_S05_P4.m4a` | 2.475 | direct;  |
| `raw/setB_chill/S05/B_S5_P5_chill.m4a` | `recordings/ch_S05_P5.m4a` | 6.059 | direct;  |
| `raw/setB_chill/S05/B_S5_R1_chill.m4a` | `recordings/ch_S05_R1.m4a` | 2.901 | direct;  |
| `raw/setB_chill/S05/B_S5_P6_chill.m4a` | `recordings/ch_S05_P6.m4a` | 2.987 | direct;  |
| `raw/setB_chill/S05/B_S5_P7_chill.m4a` | `recordings/ch_S05_P7.m4a` | 2.816 | direct;  |
| `raw/setB_chill/S06/B_S6_P0_chill.m4a` | `recordings/ch_S06_P0.m4a` | 2.731 | direct;  |
| `raw/setB_chill/S06/B_S6_P1_chill.m4a` | `recordings/ch_S06_P1.m4a` | 3.925 | direct;  |
| `raw/setB_chill/S06/B_S6_P2_chill.m4a` | `recordings/ch_S06_P2.m4a` | 5.291 | direct;  |
| `raw/setB_chill/S06/B_S6_P3_chill.m4a` | `recordings/ch_S06_P3.m4a` | 2.901 | direct;  |
| `raw/setB_chill/S06/B_S6_F1_chill.m4a` | `recordings/ch_S06_F1.m4a` | 3.925 | direct;  |
| `raw/setB_chill/S06/B_S6_P4_chill.m4a` | `recordings/ch_S06_P4.m4a` | 2.645 | direct;  |
| `raw/setB_chill/S06/B_S6_P5_chill.m4a` | `recordings/ch_S06_P5.m4a` | 4.181 | direct;  |
| `raw/setB_chill/S06/B_S6_R1_chill.m4a` | `recordings/ch_S06_R1.m4a` | 2.987 | direct;  |
| `raw/setB_chill/S06/B_S6_P6_chill.m4a` | `recordings/ch_S06_P6.m4a` | 2.560 | direct;  |
| `raw/setB_chill/S06/B_S6_P7_chill.m4a` | `recordings/ch_S06_P7.m4a` | 2.389 | direct;  |
| `raw/setB_chill/S07/B_S7_P0_chill.m4a` | `recordings/ch_S07_P0.m4a` | 2.645 | direct;  |
| `raw/setB_chill/S07/B_S7_P1_chill.m4a` | `recordings/ch_S07_P1.m4a` | 3.925 | direct;  |
| `raw/setB_chill/S07/B_S7_P2_chill.m4a` | `recordings/ch_S07_P2.m4a` | 5.461 | direct;  |
| `raw/setB_chill/S07/B_S7_P3_chill.m4a` | `recordings/ch_S07_P3.m4a` | 3.840 | direct;  |
| `raw/setB_chill/S07/B_S7_F1_chill.m4a` | `recordings/ch_S07_F1.m4a` | 5.035 | direct;  |
| `raw/setB_chill/S07/B_S7_P4_chill.m4a` | `recordings/ch_S07_P4.m4a` | 3.413 | direct;  |
| `raw/setB_chill/S07/B_S7_P5_chill.m4a` | `recordings/ch_S07_P5.m4a` | 6.571 | direct;  |
| `raw/setB_chill/S07/B_S7_R1_chill.m4a` | `recordings/ch_S07_R1.m4a` | 2.731 | direct;  |
| `raw/setB_chill/S07/B_S7_P6_chill.m4a` | `recordings/ch_S07_P6.m4a` | 4.864 | direct;  |
| `raw/setB_chill/S07/B_S7_P7_chill.m4a` | `recordings/ch_S07_P7.m4a` | 3.925 | direct;  |
| `raw/setB_chill/S07/B_S7_F3_chill.m4a` | `` | 3.499 | unexpected_row_do_not_copy; Unexpected named row; no destination approved. F2 is missing; possible F3→F2 correction requires explicit confirmation. |
| `raw/setB_chill/S08/B_S8_P0_chill.m4a` | `recordings/ch_S08_P0.m4a` | 3.499 | direct;  |
| `raw/setB_chill/S08/B_S8_P1_chill.m4a` | `recordings/ch_S08_P1.m4a` | 4.949 | direct;  |
| `raw/setB_chill/S08/B_S8_P2_chill.m4a` | `recordings/ch_S08_P2.m4a` | 4.352 | direct;  |
| `raw/setB_chill/S08/B_S8_P3_chill.m4a` | `recordings/ch_S08_P3.m4a` | 3.328 | direct;  |
| `raw/setB_chill/S08/B_S8_F1_chill.m4a` | `recordings/ch_S08_F1.m4a` | 4.096 | direct;  |
| `raw/setB_chill/S08/B_S8_F2_chill.m4a` | `recordings/ch_S08_F2.m4a` | 2.987 | direct;  |
| `raw/setB_chill/S08/B_S8_P4_chill.m4a` | `recordings/ch_S08_P4.m4a` | 5.547 | direct;  |
| `raw/setB_chill/S08/B_S8_P5_chill.m4a` | `recordings/ch_S08_P5.m4a` | 3.669 | direct;  |
| `raw/setB_chill/S08/B_S8_R1_chill.m4a` | `recordings/ch_S08_R1.m4a` | 2.901 | direct;  |
| `raw/setB_chill/S08/B_S8_P6_chill.m4a` | `recordings/ch_S08_P6.m4a` | 2.645 | direct;  |
| `raw/setB_chill/S08/B_S8_P7_chill.m4a` | `recordings/ch_S08_P7.m4a` | 2.816 | direct;  |
| `raw/setB_chill/S09/B_S9_P0_chill.m4a` | `recordings/ch_S09_P0.m4a` | 3.072 | direct;  |
| `raw/setB_chill/S09/B_S9_P1_chill.m4a` | `recordings/ch_S09_P1.m4a` | 4.352 | direct;  |
| `raw/setB_chill/S09/B_S9_P2_chill.m4a` | `recordings/ch_S09_P2.m4a` | 7.509 | direct;  |
| `raw/setB_chill/S09/B_S9_P3_chill.m4a` | `recordings/ch_S09_P3.m4a` | 2.731 | direct;  |
| `raw/setB_chill/S09/B_S9_P4_chill.m4a` | `recordings/ch_S09_P4.m4a` | 5.376 | direct;  |
| `raw/setB_chill/S09/B_S9_P5_chill.m4a` | `recordings/ch_S09_P5.m4a` | 4.181 | direct;  |
| `raw/setB_chill/S09/B_S9_R1_chill.m4a` | `recordings/ch_S09_R1.m4a` | 2.475 | direct;  |
| `raw/setB_chill/S09/B_S9_P6_chill.m4a` | `recordings/ch_S09_P6.m4a` | 2.645 | direct;  |
| `raw/setB_chill/S09/B_S9_P7_chill.m4a` | `recordings/ch_S09_P7.m4a` | 3.669 | direct;  |
| `raw/setB_chill/S10/B_S10_P0_chill.m4a` | `recordings/ch_S10_P0.m4a` | 2.901 | direct;  |
| `raw/setB_chill/S10/B_S10_P1_chill.m4a` | `recordings/ch_S10_P1.m4a` | 6.827 | direct;  |
| `raw/setB_chill/S10/B_S10_P2_chill.m4a` | `recordings/ch_S10_P2.m4a` | 5.035 | direct;  |
| `raw/setB_chill/S10/B_S10_P3_chill.m4a` | `recordings/ch_S10_P3.m4a` | 5.120 | direct;  |
| `raw/setB_chill/S10/B_S10_F1_chill.m4a` | `recordings/ch_S10_F1.m4a` | 3.499 | direct;  |
| `raw/setB_chill/S10/B_S10_P4_chill.m4a` | `recordings/ch_S10_P4.m4a` | 2.731 | direct;  |
| `raw/setB_chill/S10/B_S10_P5_chill.m4a` | `recordings/ch_S10_P5.m4a` | 4.949 | direct;  |
| `raw/setB_chill/S10/B_S10_R1_chill.m4a` | `recordings/ch_S10_R1.m4a` | 3.499 | direct;  |
| `raw/setB_chill/S10/B_S10_P6_chill.m4a` | `recordings/ch_S10_P6.m4a` | 2.645 | direct;  |
| `raw/setB_chill/S10/B_S10_P7_chill.m4a` | `recordings/ch_S10_P7.m4a` | 2.731 | direct;  |
| `raw/setB_tm/S01/B_S01_P0.m4a` | `recordings/tm_S01_P0.m4a` | 3.007 | direct;  |
| `raw/setB_tm/S01/B_S01_P1.m4a` | `recordings/tm_S01_P1.m4a` | 4.351 | direct;  |
| `raw/setB_tm/S01/B_S01_P2.m4a` | `recordings/tm_S01_P2.m4a` | 4.372 | direct;  |
| `raw/setB_tm/S01/B_S01_P3.m4a` | `recordings/tm_S01_P3.m4a` | 3.007 | direct;  |
| `raw/setB_tm/S01/B_S01_F(measured).m4a` | `recordings/tm_S01_F1.m4a` | 4.393 | inferred_from_label_confirm;  |
| `raw/setB_tm/S01/B_S01_F(chills).m4a` | `recordings/tm_S01_F2.m4a` | 2.943 | inferred_from_label_confirm;  |
| `raw/setB_tm/S01/B_S01_P4.m4a` | `recordings/tm_S01_P4.m4a` | 3.049 | direct;  |
| `raw/setB_tm/S01/B_S01_P5.m4a` | `recordings/tm_S01_P5.m4a` | 3.007 | direct;  |
| `raw/setB_tm/S01/B_S01_R1.m4a` | `recordings/tm_S01_R1.m4a` | 2.089 | direct;  |
| `raw/setB_tm/S01/B_S01_P6.m4a` | `recordings/tm_S01_P6.m4a` | 2.836 | direct;  |
| `raw/setB_tm/S01/B_S01_P7.m4a` | `recordings/tm_S01_P7.m4a` | 2.559 | direct;  |
| `raw/setB_tm/S02/B_S02_P0.m4a` | `recordings/tm_S02_P0.m4a` | 2.836 | direct;  |
| `raw/setB_tm/S02/B_S02_P1.m4a` | `recordings/tm_S02_P1.m4a` | 3.327 | direct;  |
| `raw/setB_tm/S02/B_S02_P2.m4a` | `recordings/tm_S02_P2.m4a` | 5.012 | direct;  |
| `raw/setB_tm/S02/B_S02_P3.m4a` | `recordings/tm_S02_P3.m4a` | 2.708 | direct;  |
| `raw/setB_tm/S02/B_S02_F(where).m4a` | `recordings/tm_S02_F1.m4a` | 3.796 | inferred_from_label_confirm;  |
| `raw/setB_tm/S02/B_S02_F(pain).m4a` | `recordings/tm_S02_F2.m4a` | 2.559 | inferred_from_label_confirm;  |
| `raw/setB_tm/S02/B_S02_F(last BP).m4a` | `recordings/tm_S02_F3.m4a` | 4.841 | inferred_from_label_confirm;  |
| `raw/setB_tm/S02/B_S02_P4.m4a` | `recordings/tm_S02_P4.m4a` | 3.881 | direct;  |
| `raw/setB_tm/S02/B_S02_P5.m4a` | `recordings/tm_S02_P5.m4a` | 4.884 | direct;  |
| `raw/setB_tm/S02/B_S02_R1.m4a` | `recordings/tm_S02_R1.m4a` | 2.345 | direct;  |
| `raw/setB_tm/S02/B_S02_P6.m4a` | `recordings/tm_S02_P6.m4a` | 2.836 | direct;  |
| `raw/setB_tm/S02/B_S02_P7.m4a` | `recordings/tm_S02_P7.m4a` | 2.388 | direct;  |
| `raw/setB_tm/S03/B_S03_P0.m4a` | `recordings/tm_S03_P0.m4a` | 2.089 | direct;  |
| `raw/setB_tm/S03/B_S03_P1.m4a` | `recordings/tm_S03_P1.m4a` | 4.052 | direct;  |
| `raw/setB_tm/S03/B_S03_P2.m4a` | `recordings/tm_S03_P2.m4a` | 5.012 | direct;  |
| `raw/setB_tm/S03/B_S03_P3.m4a` | `recordings/tm_S03_P3.m4a` | 3.796 | direct;  |
| `raw/setB_tm/S03/B_S03_F(where).m4a` | `recordings/tm_S03_F1.m4a` | 4.713 | inferred_from_label_confirm;  |
| `raw/setB_tm/S03/B_S03_F(pain).m4a` | `recordings/tm_S03_F2.m4a` | 1.919 | inferred_from_label_confirm;  |
| `raw/setB_tm/S03/B_S03_P4.m4a` | `recordings/tm_S03_P4.m4a` | 5.588 | direct;  |
| `raw/setB_tm/S03/B_S03_P5.m4a` | `recordings/tm_S03_P5.m4a` | 5.716 | direct;  |
| `raw/setB_tm/S03/B_S03_R1.m4a` | `recordings/tm_S03_R1.m4a` | 2.132 | direct;  |
| `raw/setB_tm/S03/B_S03_P6.m4a` | `recordings/tm_S03_P6.m4a` | 1.897 | direct;  |
| `raw/setB_tm/S03/B_S03_P7.m4a` | `recordings/tm_S03_P7.m4a` | 3.519 | direct;  |
| `raw/setB_tm/S04/B_S04_P0.m4a` | `recordings/tm_S04_P0.m4a` | 3.412 | direct;  |
| `raw/setB_tm/S04/B_S04_P1.m4a` | `recordings/tm_S04_P1.m4a` | 6.079 | direct;  |
| `raw/setB_tm/S04/B_S04_P2.m4a` | `recordings/tm_S04_P2.m4a` | 4.457 | direct;  |
| `raw/setB_tm/S04/B_S04_P3.m4a` | `recordings/tm_S04_P3.m4a` | 2.601 | direct;  |
| `raw/setB_tm/S04/B_S04_F(phlegm).m4a` | `recordings/tm_S04_F1.m4a` | 3.540 | inferred_from_label_confirm;  |
| `raw/setB_tm/S04/B_S04_F(breathless).m4a` | `recordings/tm_S04_F2.m4a` | 2.793 | inferred_from_label_confirm;  |
| `raw/setB_tm/S04/B_S04_P4.m4a` | `recordings/tm_S04_P4.m4a` | 2.623 | direct;  |
| `raw/setB_tm/S04/B_S04_P5.m4a` | `recordings/tm_S04_P5.m4a` | 2.964 | direct;  |
| `raw/setB_tm/S04/B_S04_R1.m4a` | `recordings/tm_S04_R1.m4a` | 2.281 | direct;  |
| `raw/setB_tm/S04/B_S04_P6.m4a` | `recordings/tm_S04_P6.m4a` | 5.609 | direct;  |
| `raw/setB_tm/S04/B_S04_P7.m4a` | `recordings/tm_S04_P7.m4a` | 2.473 | direct;  |
| `raw/setB_tm/S05/B_S05_P0.m4a` | `recordings/tm_S05_P0.m4a` | 1.919 | direct;  |
| `raw/setB_tm/S05/B_S05_P1.m4a` | `recordings/tm_S05_P1.m4a` | 2.665 | direct;  |
| `raw/setB_tm/S05/B_S05_P2.m4a` | `recordings/tm_S05_P2.m4a` | 3.988 | direct;  |
| `raw/setB_tm/S05/B_S05_P3.m4a` | `recordings/tm_S05_P3.m4a` | 2.004 | direct;  |
| `raw/setB_tm/S05/B_S05_F(how).m4a` | `recordings/tm_S05_F1.m4a` | 2.175 | inferred_from_label_confirm;  |
| `raw/setB_tm/S05/B_S05_P4.m4a` | `recordings/tm_S05_P4.m4a` | 3.071 | direct;  |
| `raw/setB_tm/S05/B_S05_P5.m4a` | `recordings/tm_S05_P5.m4a` | 5.503 | direct;  |
| `raw/setB_tm/S05/B_S05_R1.m4a` | `recordings/tm_S05_R1.m4a` | 1.087 | direct;  |
| `raw/setB_tm/S05/B_S05_P6.m4a` | `recordings/tm_S05_P6.m4a` | 2.025 | direct;  |
| `raw/setB_tm/S05/B_S05_P7.m4a` | `recordings/tm_S05_P7.m4a` | 2.921 | direct;  |
| `raw/setB_tm/S06/B_S06_P0.m4a` | `recordings/tm_S06_P0.m4a` | 2.452 | direct;  |
| `raw/setB_tm/S06/B_S06_P1.m4a` | `recordings/tm_S06_P1.m4a` | 2.815 | direct;  |
| `raw/setB_tm/S06/B_S06_P2.m4a` | `recordings/tm_S06_P2.m4a` | 6.164 | direct;  |
| `raw/setB_tm/S06/B_S06_P3.m4a` | `recordings/tm_S06_P3.m4a` | 1.919 | direct;  |
| `raw/setB_tm/S06/B_S06_F(last).m4a` | `recordings/tm_S06_F1.m4a` | 5.311 | inferred_from_label_confirm;  |
| `raw/setB_tm/S06/B_S06_P4.m4a` | `recordings/tm_S06_P4.m4a` | 1.513 | direct;  |
| `raw/setB_tm/S06/B_S06_P5.m4a` | `recordings/tm_S06_P5.m4a` | 3.540 | direct;  |
| `raw/setB_tm/S06/B_S06_R1.m4a` | `recordings/tm_S06_R1.m4a` | 1.577 | direct;  |
| `raw/setB_tm/S06/B_S06_P6.m4a` | `recordings/tm_S06_P6.m4a` | 1.513 | direct;  |
| `raw/setB_tm/S06/B_S06_P7.m4a` | `recordings/tm_S06_P7.m4a` | 2.367 | direct;  |
| `raw/setB_tm/S07/B_S07_P0.m4a` | `recordings/tm_S07_P0.m4a` | 1.897 | direct;  |
| `raw/setB_tm/S07/B_S07_P1.m4a` | `recordings/tm_S07_P1.m4a` | 2.516 | direct;  |
| `raw/setB_tm/S07/B_S07_P2.m4a` | `recordings/tm_S07_P2.m4a` | 4.308 | direct;  |
| `raw/setB_tm/S07/B_S07_P3.m4a` | `recordings/tm_S07_P3.m4a` | 2.687 | direct;  |
| `raw/setB_tm/S07/B_S07_F(where).m4a` | `recordings/tm_S07_F1.m4a` | 2.516 | inferred_from_label_confirm;  |
| `raw/setB_tm/S07/B_S07_F(pain).m4a` | `recordings/tm_S07_F2.m4a` | 2.217 | inferred_from_label_confirm;  |
| `raw/setB_tm/S07/B_S07_P4.m4a` | `recordings/tm_S07_P4.m4a` | 3.007 | direct;  |
| `raw/setB_tm/S07/B_S07_P5.m4a` | `recordings/tm_S07_P5.m4a` | 5.887 | direct;  |
| `raw/setB_tm/S07/B_S07_R1.m4a` | `recordings/tm_S07_R1.m4a` | 1.812 | direct;  |
| `raw/setB_tm/S07/B_S07_P6.m4a` | `recordings/tm_S07_P6.m4a` | 3.177 | direct;  |
| `raw/setB_tm/S07/B_S07_P7.m4a` | `recordings/tm_S07_P7.m4a` | 1.919 | direct;  |
| `raw/setB_tm/S08/B_S08_P0.m4a` | `recordings/tm_S08_P0.m4a` | 2.132 | direct;  |
| `raw/setB_tm/S08/B_S08_P1.m4a` | `recordings/tm_S08_P1.m4a` | 2.153 | direct;  |
| `raw/setB_tm/S08/B_S08_P2.m4a` | `recordings/tm_S08_P2.m4a` | 2.537 | direct;  |
| `raw/setB_tm/S08/B_S08_P3.m4a` | `recordings/tm_S08_P3.m4a` | 2.879 | direct;  |
| `raw/setB_tm/S08/B_S08_F(where).m4a` | `recordings/tm_S08_F1.m4a` | 2.409 | inferred_from_label_confirm;  |
| `raw/setB_tm/S08/B_S08_F(pain).m4a` | `recordings/tm_S08_F2.m4a` | 3.241 | inferred_from_label_confirm;  |
| `raw/setB_tm/S08/B_S08_P4.m4a` | `recordings/tm_S08_P4.m4a` | 4.756 | direct;  |
| `raw/setB_tm/S08/B_S08_P5.m4a` | `recordings/tm_S08_P5.m4a` | 2.473 | direct;  |
| `raw/setB_tm/S08/B_S08_R1.m4a` | `recordings/tm_S08_R1.m4a` | 2.601 | direct;  |
| `raw/setB_tm/S08/B_S08_P6.m4a` | `recordings/tm_S08_P6.m4a` | 1.876 | direct;  |
| `raw/setB_tm/S08/B_S08_P7.m4a` | `recordings/tm_S08_P7.m4a` | 1.983 | direct;  |
| `raw/setB_tm/S09/B_S09_P0.m4a` | `recordings/tm_S09_P0.m4a` | 2.025 | direct;  |
| `raw/setB_tm/S09/B_S09_P1.m4a` | `recordings/tm_S09_P1.m4a` | 2.559 | direct;  |
| `raw/setB_tm/S09/B_S09_P2.m4a` | `recordings/tm_S09_P2.m4a` | 7.508 | direct;  |
| `raw/setB_tm/S09/B_S09_P3.m4a` | `recordings/tm_S09_P3.m4a` | 2.793 | direct;  |
| `raw/setB_tm/S09/B_S09_P4.m4a` | `recordings/tm_S09_P4.m4a` | 3.732 | direct;  |
| `raw/setB_tm/S09/B_S09_P5.m4a` | `recordings/tm_S09_P5.m4a` | 4.287 | direct;  |
| `raw/setB_tm/S09/B_S09_R1.m4a` | `recordings/tm_S09_R1.m4a` | 1.983 | direct;  |
| `raw/setB_tm/S09/B_S09_P6.m4a` | `recordings/tm_S09_P6.m4a` | 1.727 | direct;  |
| `raw/setB_tm/S09/B_S09_P7.m4a` | `recordings/tm_S09_P7.m4a` | 4.948 | direct;  |
| `raw/setB_tm/S10/B_S10_P0.m4a` | `recordings/tm_S10_P0.m4a` | 2.047 | direct;  |
| `raw/setB_tm/S10/B_S10_P1.m4a` | `recordings/tm_S10_P1.m4a` | 2.793 | direct;  |
| `raw/setB_tm/S10/B_S10_P2.m4a` | `recordings/tm_S10_P2.m4a` | 5.311 | direct;  |
| `raw/setB_tm/S10/B_S10_P3.m4a` | `recordings/tm_S10_P3.m4a` | 4.799 | direct;  |
| `raw/setB_tm/S10/B_S10_F(measured).m4a` | `recordings/tm_S10_F1.m4a` | 2.857 | inferred_from_label_confirm;  |
| `raw/setB_tm/S10/B_S10_P4.m4a` | `recordings/tm_S10_P4.m4a` | 1.876 | direct;  |
| `raw/setB_tm/S10/B_S10_P5.m4a` | `recordings/tm_S10_P5.m4a` | 5.951 | direct;  |
| `raw/setB_tm/S10/B_S10_R1.m4a` | `recordings/tm_S10_R1.m4a` | 1.983 | direct;  |
| `raw/setB_tm/S10/B_S10_P6.m4a` | `recordings/tm_S10_P6.m4a` | 2.665 | direct;  |
| `raw/setB_tm/S10/B_S10_P7.m4a` | `recordings/tm_S10_P7.m4a` | 1.663 | direct;  |

## Copy gate

Confirm the semantic follow-up order and resolve ch S02/P2–P3 plus ch S07/F2–F3 before copying. No files have been copied by this inventory.
