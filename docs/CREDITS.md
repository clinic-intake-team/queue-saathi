# Gnani API costs (measured Nov 1, 2026)

From the app.gnani.ai usage history after the Step 0 test (dev key):

| Model | Usage | Cost | Rate |
|---|---|---|---|
| prisma-v3.0 (STT) | 0.17 min (≈10 s clip) | ₹0.08 per call | ≈ ₹0.47 per minute of audio |
| timbre-v3.0 (TTS) | 74 characters | ₹0.20 | ≈ ₹2.70 per 1,000 characters |

Step 0 total: ₹0.36. Balance still shows ~4.9k (assumed 1 credit = ₹1).

**Project estimate:** about ₹100–150 in total (full eval ≈ 80 min of audio ≈ ₹38; prompt cache ≈ ₹4; dev and demos ≈ ₹30–70). Credits are not a constraint. Expand the evaluation instead of trimming it. Keep caching and logging as good practice.

## First finding (single clip, anecdotal)
Clip: "Main Telma chaalis aur Glycomet leta hoon, aur do din se bukhaar hai." (~10 s, hi-IN detected)
- Without keyterms: "मैं Telmacol और Glycomet लेता हूँ और 2 दिन से बुखार भी है।" (brand + strength merged into a non-word)
- With keyterms: "मैं Telma 40 और Glycomet लेता हूँ, और दो दिन से बुखार भी है।" (correct)
- Note: same audio and `format=transcribe`, but numbers came back as a digit ("2") in one run and a word ("दो") in the other. Extraction must handle both.
- Latency: 0.5–0.7 s per STT call.
