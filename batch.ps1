# Batch-transcribe a whole folder into one document (Windows).
#
# Usage (from PowerShell in the project root):
#   .\batch.ps1 --input C:\path\to\folder --languages ru,uk,en --model small --format md
#
# All arguments are passed straight through to `python -m app.batch`
# (run `.\batch.ps1 --help` to see them).
#
# The process runs in the invoking directory, because relative paths the user
# typed resolve from there. Node is not needed: batch mode never touches the
# frontend.
#
# If Windows blocks the script:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

$ErrorActionPreference = "Stop"

$callerPwd = (Get-Location).Path

. "$PSScriptRoot\preflight.ps1"

$python = Invoke-TimbrePreflight -NeedNode $false
if (-not $python) { exit 1 }

$venvPython = Join-Path $PSScriptRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "-> Creating Python virtual environment..." -ForegroundColor Cyan
    if ($python -eq "py") { & py -3 -m venv (Join-Path $PSScriptRoot "backend\.venv") }
    else { & python -m venv (Join-Path $PSScriptRoot "backend\.venv") }
}

Write-Host "-> Installing backend dependencies..." -ForegroundColor Cyan
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -r (Join-Path $PSScriptRoot "backend\requirements.txt")

$env:PYTHONPATH = Join-Path $PSScriptRoot "backend"
Push-Location $callerPwd
try {
    & $venvPython -m app.batch @args
} finally {
    Pop-Location
}
