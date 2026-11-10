@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv. Create it with py -3.12 -m venv .venv and install requirements.txt.
  exit /b 1
)
".venv\Scripts\python.exe" "scripts\dev.py" %*
exit /b %errorlevel%
