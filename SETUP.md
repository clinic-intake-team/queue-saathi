# Run QueueSaathi locally

The web app runs with **React + FastAPI**. You can try the complete mock flow without API keys. Mock responses are labelled sample data and do not recognise your speech.

## Prerequisites

- Python **3.12 or newer** (the launcher uses Python 3.12 syntax).
- Node.js **22.18+** with npm (also supports the TypeScript-based Node tests).
- A browser with microphone permission for recording.
- ffmpeg on PATH, or the `imageio-ffmpeg` fallback installed through `requirements.txt`.

Clone the repository and enter its folder. All commands below run from the repository root.

## macOS / Linux

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
npm --prefix web ci
cp -n config/env.example .env
./start.sh --prod
```

Open **http://127.0.0.1:8000**. API documentation is at **http://127.0.0.1:8000/api/docs**. Use Ctrl+C to stop.

If port 8000 is occupied:

```sh
PORT=8020 ./start.sh --prod
```

Then open http://127.0.0.1:8020.

## Windows — PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm --prefix web ci
if (!(Test-Path .env)) { Copy-Item config/env.example .env }
.\start.ps1 --prod
```

If PowerShell blocks local scripts, use `start.bat --prod` from Command Prompt, or run the Python launcher directly:

```powershell
.\.venv\Scripts\python.exe scripts/dev.py --prod
```

To change the port in PowerShell, set `$env:PORT = '8020'` before starting.

## Development mode

Omit `--prod`:

```sh
./start.sh
```

On Windows use `start.bat` or `start.ps1`. Open **http://127.0.0.1:5173**. Vite proxies API requests to FastAPI on port 8000 (or `PORT`). Production serving builds and serves the frontend on the API's port; development uses two local processes.

## Try the mock app

1. Open `/intake`, choose a language, and start a new intake.
2. Record an answer or use the labelled mock controls. Mock answers are fixed examples, not transcriptions of the recording.
3. Review a transcript, try recording again, and confirm or correct medicines.
4. Open `/doctor` and use the demo PIN **1234**. The queue starts empty: mock/synthetic intakes are intentionally hidden. Live completed intakes and urgent partial live intakes are listed; offline summary tests exercise those display rules without provider calls.
5. Open `/results` for versioned metrics and evaluation context.

No `.env` is required for mock startup. The public `config/env.example` contains blank provider-key fields; `.env*` files are ignored. The launcher sets `GNANI_MOCK=1` unless `--live` is explicitly supplied, even if a local `.env` requests live mode.

## Live mode — optional, uses provider credits

Fill `GNANI_API_KEY` and `GROQ_API_KEY` in your local `.env`. The template selects Groq's `openai/gpt-oss-120b` with medium reasoning. Then run:

```sh
./start.sh --prod --live
```

Fixed Timbre questions are shipped in `assets/prompts/` (Hinglish) and `assets/prompts/hi/` / `en/`, with validation manifests. These are only the app's fixed questions, not patient recordings. Their playback is cache-only; missing or invalid files do not silently trigger synthesis. Mock-generated question audio is silent by design.

Live answer submissions can call Prisma and Groq; dynamic medicine read-back can call Timbre. Changed answers, evidence repair and retries may add calls. Use `.venv/bin/python scripts/dev.py --preflight` for the current call plan. Generating missing fixed prompts requires a separate explicit `--live --prepare-fixed-prompts` invocation; see the README.

Windows equivalents use `.venv\Scripts\python.exe` or `start.bat`.

## Verification — offline providers

```sh
python -m unittest discover -s tests
npm --prefix web run build
node --test tests/doctor-summary.test.mjs
```

Run these with the virtual environment active, or use its Python executable explicitly. Provider tests patch network requests rather than consuming credits. Browser checks under `scripts/check_*.py` are additional checks and may need a running app and Playwright/Chrome; they are not required to launch the app.

The separately versioned evaluation runners require local recordings and, for re-extraction or rescoring, their recorded caches. Those private inputs are intentionally not shipped. Historical protocol hashes are retained for provenance and may reject changed code; do not regenerate an official held-out result as if it were a fresh held-out evaluation.

## Troubleshooting

- **Missing npm:** install a standard Node.js distribution with npm; the app does not require this developer's cached runtime.
- **Address already in use:** stop the old server or choose a different `PORT`.
- **Frontend changes are not visible:** stop and rerun `--prod` to rebuild; refreshing only reloads the existing build.
- **Microphone blocked:** allow permission and use localhost; remote deployment needs HTTPS.
- **Doctor queue is empty:** only genuine recorded live intakes and urgent partial live intakes are listed. Mock samples are intentionally hidden.
- **No recognised speech in mock mode:** expected—mock mode uses canned answers and is always labelled.

Demo uses a simple clinic PIN. A real deployment would use proper staff authentication and encrypted storage. QueueSaathi collects information and does not diagnose or replace a clinician's full assessment.
