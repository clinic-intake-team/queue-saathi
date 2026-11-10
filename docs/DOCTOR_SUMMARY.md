# Clinical-first doctor summary

Default page: /doctor. Developer details: /doctor?debug=1.

The top paragraph and copy text are produced by web/src/doctor-summary.ts from
accepted fields and app-flow applicability metadata, without any new LLM call.
The paragraph retains unknowns and does not turn missing history into negative
findings. A valid empty symptom list at a routine visit is described as no current
symptoms **reported**, not an independently established clinical finding.

- Positive safety flags are red at the top, even alongside uncertainty. Pure
  needs_check is amber.
- Only expected unresolved information, unknown medicine identities, patient
  read-back corrections and refusals enter Needs attention. Empty box is hidden.
- Content-only fields retain evidence quotes and available audio. Identical visit
  reason/complaint is merged. Inapplicable duration/follow-ups share a muted line.
- Old records whose duration was actually asked use Not applicable, not Not asked.
- Full transcripts use a closed details section. Per-answer source badges, calls,
  token counts and raw JSON appear only with debug=1. Call counts are not fetched
  otherwise. One header chip identifies the selected record's LIVE/MOCK mode.
- Copy summary includes the narrative, content fields/evidence, relevant warnings
  and applicability notes. It excludes developer data. A selectable-text fallback
  is shown if clipboard access is denied.
- Queue rows show token, accepted age/sex, up to four words of visit reason, status
  and elapsed time, updated locally every 30 seconds.

Routine routing is in app/api/flow_rules.py. It bypasses P3 and marks follow-ups
inapplicable when a routine purpose has no accepted positive symptoms, or when a
clear global symptom denial is present. Explicit denial is preserved as a typed
app field with exact evidence. Raw extractor results are kept unchanged. Positive
red flags still interrupt and real symptoms keep the duration question. Re-record
restores flow metadata with the prior answer snapshot.

Verification: 94 Python tests, eight deterministic-summary tests and production
TypeScript/Vite build pass. Tests cover routine/no-symptom re-asks, positive safety
interruptions, correcting prior answers, missing versus negative history, unknown
medicines, refusals, duplicate fields, copying and time formatting. Extraction,
red-flag and evaluator source hashes are unchanged. No screenshots or paid test
calls were made for this redesign.

## Urgent partial intakes

A positive alert saves `status=red_flag`, `intake_complete=false` and `stopped_at`
immediately, before alert-audio work. The queue includes these live sessions
without requiring the remaining recordings, and sorts them before completed
records. Synthetic sessions remain excluded. `GET /sessions` uses the same
red-flag priority; earlier records without the completion flag remain readable.

The first banner shows the reported safety symptoms, exact patient evidence and
recorded audio. The summary retains collected information; unasked fields cannot
produce negative assertions, even if stale defaults exist. A muted early-stop
note lists the remaining fields as **Not asked**. The clipboard summary includes
red-flag evidence and the early-stop note too.

**Theek hai** returns to language selection. Kiosk alerts reset after 30 seconds;
normal completion retains its 15-second reset. Neither reset starts a new session
or triggers providers until the next patient presses Start.
