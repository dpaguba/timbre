# Shared prerequisite checks for start.ps1 and dev.ps1.
# Dot-source it: . "$PSScriptRoot\preflight.ps1"
#
# Every check fails with the command to run rather than a raw error, so a
# missing tool is a one-line fix instead of a failure three steps later.
#
# ffmpeg is deliberately not checked: decoding goes through PyAV, which links
# the ffmpeg libraries itself. The py launcher is preferred over python on PATH.
# PowerShell 7.4 turns a non-zero native exit code into a terminating error when
# $ErrorActionPreference is "Stop", which both callers set, so the version probe
# is guarded: without that, an old Python produces a raw PowerShell error rather
# than the message preflight exists to give.

function Test-TimbreCommand($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

function Invoke-TimbrePreflight {
    param([bool]$NeedNode = $true)


    $python = if (Test-TimbreCommand "py") { "py" } elseif (Test-TimbreCommand "python") { "python" } else { $null }
    if (-not $python) {
        Write-Host "Python 3.10+ was not found. Install it from https://python.org" -ForegroundColor Red
        Write-Host "Make sure to tick 'Add python.exe to PATH' during installation."
        return $null
    }

    $previousNativePreference = $PSNativeCommandUseErrorActionPreference
    try {
        $PSNativeCommandUseErrorActionPreference = $false
        $null = & $python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>&1
        $pythonVersionExit = $LASTEXITCODE
        $null = & $python -c "import ensurepip" 2>&1
        $ensurepipExit = $LASTEXITCODE
    } finally {
        $PSNativeCommandUseErrorActionPreference = $previousNativePreference
    }

    if ($ensurepipExit -ne 0) {
        Write-Host "This Python cannot create virtual environments (ensurepip is missing)." -ForegroundColor Red
        Write-Host "Reinstall Python from https://python.org rather than the Store build."
        return $null
    }

    if ($pythonVersionExit -ne 0) {
        $found = & $python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
        Write-Host "Python 3.10 or newer is required, found $found." -ForegroundColor Red
        return $null
    }

    if ($NeedNode) {
        if (-not (Test-TimbreCommand "node") -or -not (Test-TimbreCommand "npm")) {
            Write-Host "Node.js was not found. Install the LTS release from https://nodejs.org" -ForegroundColor Red
            Write-Host "It is needed to build the frontend."
            return $null
        }
        $nodeMajor = [int](((node -v) -replace '^v', '') -split '\.')[0]
        if ($nodeMajor -lt 18) {
            Write-Host "Node.js 18 or newer is required, found $(node -v)." -ForegroundColor Red
            return $null
        }
    }

    return $python
}
