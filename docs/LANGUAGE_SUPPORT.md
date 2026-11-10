# Language preferences

Implemented independent home/patient controls for interface language and question
language: Hindi (Devanagari), English and Hinglish. Choices persist locally and
question language is stored in each session. Changing language keeps the answers.
Original transcripts and evidence are never translated. Clinical extraction and
doctor-record content retain the existing English schema.

All 20 question/retry/alert/follow-up texts have Hindi and English translations.
Dynamic medicine read-back uses the question language and preserves medicine
names. STT keeps bilingual hi-IN,en-IN support, allowing patients to answer in
either language regardless of the question language.

## Voice audio status

Existing Hinglish audio is preserved. Following explicit user approval, all 20
Hindi and 20 English fixed clips were generated and cached. Each clip was
validated as a non-silent PCM16 WAV and served successfully by the audio endpoint. Cache paths:

- Hinglish: assets/prompts/<id>.wav
- Hindi: assets/prompts/hi/<id>.wav
- English: assets/prompts/en/<id>.wav

Preparing both additional fixed caches used exactly 40 one-time Timbre HTTP
calls, with no extra retry calls. Each cache is reused thereafter; only dynamic medicine read-back can
synthesize speech at runtime. The existing bilingual Shivani hi-en voice is used
with the selected-language text. Explicit generation commands are documented in
README. Both language-generation commands completed successfully.

## Verification

89 Python tests pass, including independent persisted choices, all 20 translation
keys, language-isolated audio caches, language-aware STT question context and
missing-audio behavior without automatic fixed generation. TypeScript/Vite build
passes. The screenshot-free language browser check was declined; it was not run.
No screenshots were taken. scripts/check_languages.py uses mocked API routes if
browser verification is permitted later.

## Audio completion audit

`logs/language_audio_audit.json` confirms 20 Hindi + 20 English + 20 unchanged
Hinglish clips are valid and served by the app, with exactly 40 new Timbre calls
and zero new Prisma/Groq calls. Refresh the page to update language-cache status,
then tap Replay question if browser autoplay requires a gesture.
