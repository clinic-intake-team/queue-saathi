# Run from any directory. All flags are passed through to the Python launcher.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    Write-Error 'Missing .venv. Run: py -3.12 -m venv .venv, then install requirements.txt.'
    exit 1
}
& $python (Join-Path $PSScriptRoot 'scripts\dev.py') @args
exit $LASTEXITCODE
