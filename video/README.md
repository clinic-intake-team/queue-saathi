# QueueSaathi · Standalone Remotion explainer

**Final Stage 2:** `out/queuesaathi_demo.mp4`, **60.000 seconds**, 1920×1080 at 30 fps.
Eight Avinash Timbre v3.0 lines (speed 1.0; en-IN except line 2 hi-en),
real clip audio with no VO overlap, and burned-in captions. No music was supplied.
Caption spelling uses QueueSaathi and 52% → 95%.

Reproduce from the supplied local inputs:

```sh
.venv/bin/python video/scripts/prepare_final.py
.venv/bin/python video/scripts/tool.py render:final
.venv/bin/python video/scripts/finish_final.py
```

Voice-over lengths: 3.36, 2.56, 4.00, 4.16, 3.60, 4.08, 6.24, 2.80 seconds.
Line 4 extends its scene from 4.000 to 4.167s (frame rounding); line 5 from
3.000 to 3.600s. Revised line 7 extends results to 6.267s. To keep exactly
60s, logo/intake is 4s and doctor screenshots 6.633s. All clips remain at 1×
and the opening remains 3.5s. Approved revised lines 2 and 7 are referenced in
`voiceover-plan.json`; original audition files are preserved.
Final section timing and validation are saved in `out/final-timing.json` and
`out/final-validation.json`. Video/audio files remain Git-ignored.

**Earlier real-clips preview**, 59.333 seconds, 1920×1080, 30 fps, H.264/AAC MP4.
`out/preview_with_clips.mp4` replaces all three grey placeholders with the supplied
real recordings and their own audio at volume 1 and 1× speed. There is no
voice-over or music. The final `queuesaathi_demo.mp4` now adds voice-over and captions. The original 60-second silent `out/preview.mp4` is preserved.
This folder is independent of the app; no app pages, navigation, extraction
prompts or scoring rules were changed.

## Render the real-clips preview

```sh
.venv/bin/python video/scripts/tool.py render:clips
```

Or from `video/`: `npm run render:clips`. Remotion Studio exposes both
`QueueSaathiPreview` (silent placeholders) and `QueueSaathiClipPreview` (real clips).
Input media lives in ignored `public/media/`; `src/clip-metadata.json` records the
source frame counts and hashes. Hash checks prevent accidentally using changed
media without updating the edit. The originals in `~/Desktop/demo_video/` remain
unchanged.

The supplied clips already contain a dark 1920×1080 canvas. Only their actual
phone viewport (x=736, y=54, width=448, height=972) is shown inside the Remotion
phone; the old canvas is cropped in CSS without re-encoding the imported files.
Their complete audio is used without amplification, ducking or VO overlays.

| Clip | Playback interval | Clip length | Slot length |
|---|---|---:|---:|
| A | 00:11.500–00:20.767 | 9.267s | 10s; last frame held 0.733s |
| B | 00:25.500–00:32.733 | 7.233s | 8s; last frame held 0.767s |
| C | 00:33.500–00:41.333 | 7.833s | 7.833s; extended from 6s |

Subsequent starts: Reception **41.333s**, Doctor summaries **44.333s**,
Results **51.333s**, End card **56.333s**. Total **59.333s**. No clip is sped up,
looped or truncated. The opening queue is shortened to 3.5s with its animations accelerated; all later scenes move 2.5s earlier. Clip C retains its full speech.

## Preview

Open `out/preview_with_clips.mp4` for the latest edit. Original Stage 1:
`out/preview.mp4` and `out/contact-sheet.png`. Real-clip review stills are in
`out/clips-frames/`, with `out/clips-contact-sheet.png` as a quick overview.
Rendered video, future audio/video inputs, dependencies and real patient capture
images are ignored by Git. Do not add them with `git add -f`.

From the project root using this workstation's existing Node fallback:

```sh
.venv/bin/python video/scripts/tool.py typecheck
.venv/bin/python video/scripts/tool.py studio
.venv/bin/python video/scripts/tool.py render:preview
```

With Node/npm on PATH, `cd video`, then `npm ci`, `npm run studio`, or
`npm run render:preview`. The renderer uses the installed Chrome binary on macOS.
Set `REMOTION_BROWSER_EXECUTABLE` if using another machine. All Remotion packages
are pinned to the same version in `package.json` and `package-lock.json`.

Rendering uses the official [Remotion renderer](https://www.remotion.dev/docs/renderer/render-media)
and [custom browser executable option](https://www.remotion.dev/docs/options/browser-executable).
Animations depend on composition frames, springs and interpolation, not CSS
wall-clock animations, so offline renders are deterministic. Local Google Font
files reuse the app's Inter and Instrument Serif exported for the pipeline slide.
Font sources/licenses: [Inter](https://github.com/google/fonts/tree/main/ofl/inter),
[Instrument Serif](https://github.com/google/fonts/tree/main/ofl/instrumentserif).

## Real-screen provenance

`public/captures/provenance.json` records URLs, dimensions, session IDs and the
one recording-frame timestamp. These are real screenshots/recording pixels:

| File | Source |
|---|---|
| `intake-language.png` | Playwright: localhost:8020/intake?kiosk=1; 390×844; dark/Hinglish |
| `question.png` | Playwright: actual unfinished Token 14 live session, read-only resume |
| `medicine-readback.png` | Real `patient1_clean.mp4` at **01:46 (106.000s)**; Dolo 650 and both confirmation buttons visible |
| `red-alert.png` | Playwright: actual saved Token 31 live-session alert, read-only resume |
| `doctor-token-31.png` | Playwright: actual saved urgent record, 1440×900 |
| `doctor-token-14.png` | Playwright: actual saved completed record, 1440×900 |

No built-in sample/preview screens, fabricated records or redrawn app UI were
used. The red-banner highlight is a soft presentation overlay positioned using
its measured bounding box in the real screenshot. The medicine frame was cropped
to the actual app viewport; no UI was altered or generated.

To recapture from the running app, use:

```sh
.venv/bin/python video/scripts/capture.py
```

The capture script blocks session-changing requests and asserts saved session
hashes remain unchanged. It only reads existing live data and unlocks Doctor view
with the configured clinic PIN. It never submits answers, starts a session or
calls Prisma, Groq or Timbre. Keep real patient captures private.

The read-back frame can be re-extracted without altering the source video:

```sh
ffmpeg -ss 106 -i "$HOME/Desktop/demo_video/patient1_clean.mp4" -frames:v 1 \
  -vf 'crop=448:972:736:54' video/public/captures/medicine-readback.png
```

## Stage 1 timeline

| Start | End | Scene |
|---|---|---|
| 00:00 | 00:06 | Animated clinic queue, counting token, ticking clock |
| 00:06 | 00:09 | Typed patient quote in Instrument Serif |
| 00:09 | 00:14 | Logo reveal and phone with the real intake screen |
| 00:14 | 00:24 | Grey real-clip A slot |
| 00:24 | 00:28 | Speech bubble → Prisma v3.0 → Validated |
| 00:28 | 00:36 | Grey real-clip B slot |
| 00:36 | 00:42 | Grey real-clip C slot, soft red glow |
| 00:42 | 00:45 | Alert → Reception |
| 00:45 | 00:52 | Real Token 31, then Token 14 doctor screenshots |
| 00:52 | 00:57 | Recorded evaluation counters |
| 00:57 | 01:00 | Logo, tagline and Gnani credit; final frame holds |

The evaluation numbers follow `eval/results/setA_summary.csv` (30/58 → 55/58
medicine names, rounded to 52% → 95%) and `setB_summary_v4.csv` (4/4 flagged
positive cases). The 276 count is unique recordings: 40 Set A + 212 Set B + 24
Set C, not a count of API calls or independent patients. Both speakers are counted.

## Stage 2 completed

All eight Avinash WAVs are in `~/Desktop/demo_video/vo/vo01.wav` through
`vo08.wav`. The final includes the real clips with their own audio, normalised
voice-over, and burned-in captions. No optional music was supplied.
Final audio is normalised to about −16 LUFS, with a conservative −1.5 dBTP target
to keep encoded peaks below −1 dB. Source recordings are unchanged.


## Submission composition (2:30)

`Submission` is a separate 1920×1080, 30 fps composition. It preserves the
60-second compositions and `out/queuesaathi_demo.mp4`. Approved speech and real
clips are copied into ignored `public/media/submission/`; no provider calls occur
while preparing or rendering. Line 2 uses the approved hi-IN / Avinash / 0.95 WAV;
the other twelve use en-IN / Avinash / 1.0.

```sh
.venv/bin/python video/scripts/prepare_submission.py
.venv/bin/python video/scripts/tool.py typecheck
.venv/bin/python video/scripts/tool.py render:submission
.venv/bin/python video/scripts/finish_submission.py
```

The final destination is `~/Desktop/demo_video/queuesaathi_submission.mp4`.
`src/submission-timeline.json` is the frame-based timeline; review stills, timing,
protected-file hashes and the final validation report live in ignored
`out/submission/`. The finish step checks all clips and voice-over tracks against
the raw render, verifies no VO/clip overlap, validates source hashes and the old
60-second output, and measures loudness/peaks. No music file was supplied.

All app shots reuse actual saved screenshots or the approved real recordings.
Standalone pipeline, keyterm, safety, results and principle illustrations are
presentation graphics. The statistics excerpt is cropped from the real home
recording to exclude the illustrative doctor card. Evidence playback is retained
at 1× with the clip's own audio; no VO plays over it. Captions use QueueSaathi and
numeric metric spellings.
