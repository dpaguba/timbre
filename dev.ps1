# Development mode on Windows: FastAPI backend (with reload) plus the Vite dev
# server. Frontend on :5173 proxies /api to the backend on :8000
#
# The dev server is a different origin, so TIMBRE_DEV tells the backend to
# accept it. The backend runs as a background job and is stopped on exit.
#
# Usage:  .\dev.ps1

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

. "$PSScriptRoot\preflight.ps1"

$python = Invoke-TimbrePreflight -NeedNode $true
if (-not $python) { exit 1 }

$env:TIMBRE_DEV = "1"

$venvPython = Join-Path $PSScriptRoot "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "-> Creating Python virtual environment..." -ForegroundColor Cyan
    if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 -m venv backend\.venv }
    else { & python -m venv backend\.venv }
}

Write-Host "-> Installing dev dependencies..." -ForegroundColor Cyan
& $venvPython -m pip install --quiet -r backend\requirements-dev.txt

$backend = Start-Process -FilePath $venvPython `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000" `
    -WorkingDirectory (Join-Path $PSScriptRoot "backend") `
    -NoNewWindow -PassThru

try {
    Push-Location frontend
    & npm install --silent
    & npm run dev
} finally {
    Pop-Location
    if ($backend -and -not $backend.HasExited) {
        Write-Host "-> Stopping backend..." -ForegroundColor DarkGray
        Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    }
}
