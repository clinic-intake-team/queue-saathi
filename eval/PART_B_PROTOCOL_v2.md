# Part B v2 run protocol

Authorization: the user confirmed Part A and explicitly instructed running Part B. The script prints the exact cache-aware call budget before executing that authorization. Default mode remains a dry plan; --real opts in.

Only cached transcripts for P2/P3 are sent to Groq. There are zero Prisma calls. The combined comparison includes Set B's 20 P2 + 20 P3 rows, plus Set C's P2/P3 rows in both keyterm conditions. Identical full request keys are deduplicated. Different frozen B/C base prompts remain distinct keys so each dataset's requested fields are respected. All other rows retain Part A extraction outputs.

Model openai/gpt-oss-120b, medium reasoning, temperature 0, JSON object output. P2 visit_reason is separate from clinical symptoms, including explicit null when absent. Symptoms retain counts/frequency/modifiers. P3 permits zero-day onset and optional supported hours. Both prompts use general instructions, not patient-card sentences or answers.

One evidence repair per newly generated response, for all quote errors together. The repair request contains only transcript, field names and frozen candidate values/statuses; no truth, scorer verdict or expected answer. Only returned evidence strings may be applied. A failed repair remains rejected per field. This shared mechanism covers all row types in the v2 application backend; the evaluation freshly calls only P2/P3. The original app remains untouched, and app_v2 remains a UI shell with the shared backend entry point exposed.

Primary, repair and final-result caches are separate. A primary that succeeded before a daily quota stop is never paid for again on resume. Minute 429/5xx retries use the existing five-retry policy; a daily 429's actual body is the authority to checkpoint/exit. Failed HTTP transport responses never count as invalid_llm_output.

The protocol hashes v1/Part A baseline files, ground truth, source code and all request identities before paid calls. No final summary is printed until all requested B/C re-extractions are completed. Outputs use *_partB_v2.csv and three-way comparison CSVs. Earlier baseline outputs are protected against changes. Optional hours are recorded but unscored; the new reason field feeds the existing complaint reason concepts, with a separate supplementary reason metric. No existing complaint synonym, numeric tolerance, medicine alias or card fact is changed.
