# QueueSaathi
### Your history, before you walk in.

**Solution pitch · Great Indian AI Internship Challenge**

**The problem.** A patient waiting at a clinic may say, “BP ki goli leta hoon… naam yaad nahi.” Short consultations, forgotten medicine names and language barriers can make it hard to communicate the essential history clearly.

**Our solution.** QueueSaathi is a voice-first pre-consultation intake prototype. While waiting, patients answer short questions in Hinglish, Hindi or English. The app collects their visit reason, symptoms, duration, medicines, allergies and existing conditions. It reads medicines back so patients can confirm or correct them, preserving uncertainty when a name is unknown. Doctors receive a structured summary with the patient's quoted words and recorded audio as evidence. Routine visits can skip irrelevant questions.

**Safety by design.** Keyword screening and LLM extraction identify potential red flags. Positive findings or uncertain safety answers prompt reception review; urgent partial intakes remain visible at the top of the doctor queue. Extracted fields undergo code validation, and unusable answers can be re-asked. QueueSaathi collects information—it does not diagnose or replace a doctor's full history or emergency assessment.

**Technology.** Gnani AI's **Prisma v3.0** transcribes speech with question-specific medicine and symptom keyterms. **gpt-oss-120b via Groq** structures the transcript; Python validates the fields and applies safety checks. Gnani AI's **Timbre v3.0** voices cached questions and dynamic medicine read-back. A React interface and FastAPI backend provide the patient intake and doctor queue.

**What we measured.** Across **276 scripted recordings from two speakers**:
- Medicine-name recognition improved from **52% to 95%** with Prisma keyterms: **30/58 → 55/58 medicine mentions**, across 40 medicine-test clips. This measures names, not dosage accuracy.
- **4/4 red-flag-positive sessions** were flagged within 20 full scripted sessions.
- False alarms fell from **11/16 to 1/16** after validation and safety-logic fixes.

These recordings were used to develop and refine the prototype; the results are **not an independent clinical evaluation**. Errors remain—for example, one recording of “Telma 40” was transcribed as “Telma H.” Patient confirmation and evidence visibility are essential, and read-back does not guarantee correctness.

**Next steps.** Gather feedback from clinic staff, test with more speakers and realistic clinic noise, and extend Indian-language coverage. Real deployment would require proper staff authentication, encrypted storage and clinical validation.

**Project:** [GitHub repository](https://github.com/clinic-intake-team/Gnani_Hackathon)  
**Evaluation evidence:** [Medicine-name results](../eval/results/setA_summary.csv) · [Session evaluation guide](../eval/setB_README.md)
