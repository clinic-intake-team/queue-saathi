# Set C development evaluation: version 2

Set C is a development set for both ch and tm. These changes are explicitly authorized after reviewing version 1; results are not held-out performance. No Set B lines, S01–S10 data, or Set B recordings are used for implementation or testing.

## Validation and safety changes

Validation is per field. Type, range, shape, and status checks still apply. Evidence must be nonempty and verbatim only for non-null values (including empty lists); null-valued refusal, question and unclear fields do not require a verbatim quotation. A failing field becomes `{value: null, status: unclear, evidence: ""}` and its error is recorded; every other valid field remains. Malformed root JSON makes the requested fields unclear, without semantic retries. Sanitized results and original diagnostic errors are cached separately from version 1.

For P4 only, a non-negated mention of blood/khoon/bleeding/खून/रक्त triggers a keyword alert even without a specific vomiting or bleeding phrase. This intentionally broad rule can flag mentions such as blood tests; it is the requested conservative screen, not a diagnosis. Existing negation and symptom rules remain in use.

If a P4 field is invalid or unclear, the screen returns `needs_check` with `alert=true`; an invalid screen is never a negative screen. Incomplete P4 refusals/questions also require checking rather than being treated as a denial. The record retains the sanitized extraction and the separate screening status. `needs_check` counts as an alert in red-flag metrics, including false alarms on negative cases. The future app must re-ask or send the patient to reception; this evaluator records that disposition and does not implement a patient UI.

## Scoring changes

- C01 accepts either `unclear` or `question`, with null complaint value. This applies to both speakers.
- C07 passes when headache, severity and Monday onset are present anywhere across summary plus symptom entries; they do not have to occur in the same entry. All complaint concepts now use this combined-field check, retaining the existing fixed synonym expressions and negation handling.
- Other numeric, status, complaint-concept, and P4 extraction-value criteria remain unchanged. P4 status accuracy uses `needs_check` when screening is incomplete. P4 value accuracy requires actual extracted evidence of the expected symptom or a usable denial; an alert from the fail-safe alone is not a correct extracted value.
- `silently_wrong`: status is `ok` but value_correct is zero.
- `safe_miss`: ground truth expects status `ok` (a value), but output status is `unclear`, `declined`, or `needs_check`.
- These counts are reported overall and per speaker, separately per condition, along with status/value fractions, flags caught and false alarms. `safe_miss` means explicit uncertainty, not that all clinical risk has been resolved.

## Keyterm experiment and cache reuse

`data/symptoms.txt` is a fixed English/Hinglish symptom list established before this run. On P2 and P4, compare symptom_keyterms_off (no keyterms) against symptom_keyterms_on (the symptom list). P5 always uses medicine keyterms. P1 and P3 have no keyterms. Previous question context, Prisma model/language/format, and original M4A bytes stay unchanged.

Both conditions cover 24 clips for comparable summaries. Only 14 P2/P4 clips change STT parameters; the other 10 clips appear in both condition summaries and reuse identical responses, rather than spending for duplicate calls. The preflight counts shared requests once, while reporting cache reuse on duplicate condition entries. An extraction response with identical model/question/transcript/prompt is reused regardless of the STT condition, but sanitized with the new validation policy. The LLM prompt is unchanged to isolate validation and STT keyterm changes.

Previously captured raw or parsed responses can be revalidated without Groq calls. One historical rejected response was never retained; it cannot be reconstructed or partially recovered. Its unchanged transcript needs one new extraction under the approved version-2 policy. Newly malformed/invalid generations are cached as unclear fields and are not called repeatedly until valid.

## Output preservation

This preflight makes no API calls and does not overwrite version-1 results. On successful completion of the approved run, old CSVs are copied to `setC_per_clip_v1.csv` and `setC_summary_v1.csv` before the current files are replaced. Version-2 per-clip output has 48 rows with condition labels; summaries have 6 rows (overall/ch/tm for each condition). The protocol is fingerprinted in `eval/setC_development_v2_protocol.json`, independently of the earlier frozen protocol. Failure reports may include both development speakers. No baseline results are presented as new measurements before a real run.


# Part A v2 code-only re-score (2026-11-07)

This section is the explicitly requested amendment. The historical text above is retained unchanged and its exact original bytes are preserved in SCORING_NOTES_v1.md. In this section, v1 means the completed official Set B v1 and the latest medium-effort Set C development run-2 baseline in the untagged setC CSVs. Older Set C *_v1.csv files and the low-effort experiment are also preserved; neither is silently substituted as the comparison baseline.

## Scope and generation provenance

No prompts, models, keyterms, transcripts, ground truth or original v1 code are changed. Part A never makes Prisma, Groq or evidence-repair calls. Set B uses the original response JSON retained for all 212 rows. Set C uses retained response JSON where available and exact original parsed-generation caches otherwise, located using the frozen run-2 prompt/model/question/transcript cache key. Sanitized v1 extractions are not substituted for original raw generations when originals exist. The runner blocks network/provider entry points and verifies protected v1 file hashes after writing only *_v2 outputs.

## Validation changes

1. An ok red_flag_symptoms=[] requires no evidence. Nonempty safety lists and all other non-null values still require nonempty, verbatim evidence.
2. evidence=null normalizes to the empty string. This fixes absent optional-field evidence without inventing a quote; a nonempty safety list or another non-null value still fails if its evidence is empty/non-verbatim.
3. A bare {value,status,evidence} envelope is wrapped only when the requested field set contains exactly one field. Multi-field attribution is never guessed. This includes standalone follow_up schemas when only that field is requested; current Set B F rows request follow_up plus safety, so an ambiguous flat two-field response remains invalid.
4. Pure nested value/null wrappers normalize to outer value=null. Non-ok status then passes with null; ok/null remains invalid. A phlegm/BP object containing an optional null component is not collapsed. No missing numeric values or question keys are inferred.
5. Validation remains per field; original clinical type/range/shape checks apply. Each normalization, remaining validation error and negation override is saved separately in v2 output.

## Safety changes

The existing keyword vocabulary is reused. Hindi nasal orthographic variants are normalized for keyword scanning only, leaving transcript/evidence bytes intact. The keyword scan also identifies negated symptom mentions, including negation between symptom words. Inability phrases such as cannot breathe remain positive. A negated mention removes the matching LLM-present safety symptom and changes a validated breathless=true follow-up to false. Independent positive keyword evidence still alerts even if another mention is denied; unknown/unmatched LLM symptom labels are not silently discarded.

A same-session P4 response with a valid ok empty safety list, no safety validation error and no positive keyword/LLM flag counts as a denial. It clears only needs_check from P2/F rows that have no positive flag. P4's own needs_check always remains an alert. Positive keyword or LLM evidence from any row always alerts. Pre-resolution flags and clearing decisions remain in the v2 per-clip output.

Set C recordings are independent edge-case answers, not linked multi-question sessions. No P4 denial is borrowed from another C clip. Existing P2 Set C generations requested complaint only; no unrequested missing safety field is manufactured or counted invalid.

## Scoring changes (complete list)

- Each expected complaint concept is evaluated independently across the summary and symptom entries. Required concept components may be distributed across those passages.
- Existing chest/heaviness vocabulary is factored into anatomy and heaviness components so coordinated/shared-anatomy wording is accepted. Sentence, comma-clause and contrast boundaries keep negation local in the affirmative matching helper.
- daily/roz/roj/रोज़ variants are accepted alongside the existing frequency expressions for frequent headaches.
- Set C uses the same independent component matching policy with its existing concept vocabulary; its previous run-2 scorer already supported distributing severity/onset components across passages.
- No other synonyms, card-specific exceptions, medicine aliases, duration rules, ground-truth values or numeric tolerances are added. Raw/fuzzy medicine scoring and all metric definitions stay unchanged.

All original v1 result files stay unchanged. New results are setB_per_clip_v2.csv, setB_per_session_v2.csv, setB_summary_v2.csv, setC_per_clip_v2.csv and setC_summary_v2.csv, with side-by-side comparison CSVs and an audit ending in _v2. The Part A gate is STOP after these comparisons; P2 visit_reason, new duration prompts/hours, and one-call evidence repair belong to Part B and are not implemented or called by this run.

Part A implementation verification: negation is confined to comma-delimited clauses as well as sentence/contrast boundaries, so denying an unrelated action in a later clause cannot cancel an earlier positive symptom. Existing composite keyword detection is retained across the full answer, and independent positive keyword evidence always alerts. The first intermediate offline candidate is archived separately under results/partA_candidate1_v2; final v2 files use the corrected implementation.

A standalone denial-only prefix followed by a comma/colon is attached to the following clause; it is not carried across a sentence or contrast boundary. This preserves leading denials while preventing a later unrelated denial from erasing an earlier positive. Intermediate candidate 2 is archived under results/partA_candidate2_v2; neither intermediate candidate is the final v2 summary.
