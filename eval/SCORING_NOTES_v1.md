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
