# Starts the FastAPI dev server using the project venv's Python explicitly.
#
# Why this script exists: `uvicorn app.main:app --reload` or `python -m
# uvicorn ...` relies on ambient PATH resolution for `python`/`uvicorn`. If
# the venv isn't activated in the current shell, PATH can silently resolve
# to a *different* Python install (e.g. a system-wide one) instead of
# backend/.venv - that process still binds the port and looks like it's
# working, but it may be missing project dependencies or (if it's an old
# process from an earlier terminal that was never restarted) serving stale
# code with no visible sign anything is wrong. Bypass the whole ambiguity by
# always invoking .venv\Scripts\python.exe directly, never `python`/
# `uvicorn` bare.
#
# If you ever need to confirm what a *currently running* server is actually
# serving, don't trust `Get-Process`/`Get-CimInstance`/netstat's PID
# attribution alone - on this machine those have been observed to report a
# process's executable/command line inconsistently with what the process
# itself reports (its own `sys.executable`), and a killed process's port can
# keep showing as LISTENING in netstat briefly after it's gone. The
# reliable check is behavioral: hit the running server and look for
# something (an error string, a response shape) that only the current code
# would produce.
#
# Usage: powershell -File scripts\run-api.ps1

$ErrorActionPreference = 'Stop'

$backendRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $backendRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $venvPython)) {
    Write-Error "venv not found at $venvPython`nRun: python -m venv .venv; .venv\Scripts\pip install -r requirements.txt"
    exit 1
}

$ambient = Get-Command python -ErrorAction SilentlyContinue
if ($ambient -and ($ambient.Source -ne $venvPython)) {
    Write-Warning "Ambient 'python' on PATH resolves to $($ambient.Source), NOT the project venv ($venvPython). This script sidesteps that by invoking the venv python directly - but if you ever run uvicorn/python by hand instead of this script, you'll silently get the wrong interpreter."
}

Set-Location $backendRoot
& $venvPython -m uvicorn app.main:app --reload
