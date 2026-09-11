# Starts the Arq background worker using the project venv's Python
# explicitly. See run-api.ps1 for why this matters (ambient PATH resolution
# hazard, and why process-inspection tools alone aren't a reliable way to
# confirm what a running process is actually serving) - the same applies to
# `arq app.background.worker.WorkerSettings` run bare.
#
# Usage: powershell -File scripts\run-worker.ps1

$ErrorActionPreference = 'Stop'

$backendRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $backendRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $venvPython)) {
    Write-Error "venv not found at $venvPython`nRun: python -m venv .venv; .venv\Scripts\pip install -r requirements.txt"
    exit 1
}

$ambient = Get-Command python -ErrorAction SilentlyContinue
if ($ambient -and ($ambient.Source -ne $venvPython)) {
    Write-Warning "Ambient 'python' on PATH resolves to $($ambient.Source), NOT the project venv ($venvPython). This script sidesteps that by invoking the venv python directly - but if you ever run arq/python by hand instead of this script, you'll silently get the wrong interpreter."
}

Set-Location $backendRoot
& $venvPython -m arq app.background.worker.WorkerSettings
