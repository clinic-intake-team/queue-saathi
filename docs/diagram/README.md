# Standalone pipeline slide

Open `index.html` directly in Chrome, Edge or Firefox. No server, npm or build
step is needed. The page has inline SVG, CSS and JavaScript. Its only network
requests are Google Fonts (Inter and Instrument Serif); there are no app/API
requests. Internet access is needed for the requested Google Fonts on first use.

- Recording canvas: **1920×1080**, scaled proportionally to fit other windows.
- Use the browser's full-screen mode and reload to replay.
- Fonts load before the diagram appears, avoiding text/layout shifts.
- Nodes start at 0.5s, stagger by 0.35s, then connectors and the red branch draw.
  The complete state is visible by 3.7s; the subtle main-path pulse loops every 3s.
- `index.html?static` shows the final state without animation/pulse.
- Reduced-motion preference also shows the static state.
- The PNG is **3840×2160**, dark background. The SVG is **1920×1080** with
  used Google Font files embedded. Neither static export includes the moving pulse.

To reproduce both exports from the repository root (Playwright and Chrome required):

```sh
.venv/bin/python docs/diagram/export.py
```

This opens the standalone page, checks loaded fonts, waits for the animation,
captures the final PNG at device scale 2, and serializes the same final SVG.
It also checks reduced-motion, dimensions and browser errors. It makes no
Prisma, Groq or Timbre calls and takes no screenshots of patient data.

## Metric provenance

- `eval/results/setA_summary.csv`, overall: 30/58 = 52% without keyterms,
  55/58 = 95% with keyterms (rounded).
- `eval/results/setB_summary_v3.csv`, overall: 4/4 red flags caught and
  1/16 false alarms. These safety counts are unchanged in v4.

The diagram follows the supplied presentation labels. “ABDM OP Consultation
sections” describes summary organisation; it is not a certification claim.
The diagram is not mounted in FastAPI, the Results page or app navigation.
