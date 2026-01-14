# One-command local launcher for Timbre on Windows.
# Installs backend dependencies into a venv, rebuilds the frontend when dist is
# missing or any source file is newer than the last build, and serves the whole
# app from http://localhost:8000
#
# Usage (from PowerShell, in the project root):
#   .\start.ps1
#
# If Windows blocks the script, allow local scripts for this session first:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

. "$PSScriptRoot\preflight.ps1"

$python = Invoke-TimbrePreflight -NeedNode $true
if (-not $python) { exit 1 }

$venvPython = Join-Path $PSScriptRoot "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "-> Creating Python virtual environment..." -ForegroundColor Cyan
    if ($python -eq "py") { & py -3 -m venv backend\.venv } else { & python -m venv backend\.venv }
}

Write-Host "-> Installing backend dependencies..." -ForegroundColor Cyan
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -r backend\requirements.txt

$distIndex = "frontend\dist\index.html"
$needsBuild = $true

if (Test-Path $distIndex) {
    $builtAt = (Get-Item $distIndex).LastWriteTimeUtc
    $sources = @(Get-ChildItem -Path "frontend\src" -Recurse -File -ErrorAction SilentlyContinue)
    $sources += Get-Item "frontend\index.html", "frontend\package.json" -ErrorAction SilentlyContinue
    $newest = ($sources | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum
    if ($newest -le $builtAt) { $needsBuild = $false }
}

if ($needsBuild) {
    Write-Host "-> Building frontend..." -ForegroundColor Cyan
    Push-Location frontend
    try {
        & npm install --silent
        if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
        & npm run build
        if ($LASTEXITCODE -ne 0) { throw "npm run build failed" }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "-> Frontend is up to date." -ForegroundColor DarkGray
}

Write-Host "-> Timbre is starting on http://localhost:8000" -ForegroundColor Green
Push-Location backend
try {
    & $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
