# Archive

Earlier prototypes and historical evaluation code, kept for reproducibility. Not used by the current app.

- `app.py` and `app_v2.py`: earlier Streamlit UI prototypes. Run from the repository root if inspecting them; the second still imports the root `app_extract_v2.py` compatibility module.
- `examples/`: historical example outputs; the example scripts write here.

`redflags_v2.py` remains at the root because evaluation runners and tests import it. `app_extract_v2.py` remains there because the archived v2 prototype imports it. Protocol snapshots stay at their original paths, and recorded evaluation outputs are unchanged.

The current app uses `start.sh`, `start.ps1` or `start.bat`. See [setup](../SETUP.md).
