# Loads the Vercel + submission tasks into the LIVE hub, registers the Kaggle runbook, notifies agents,
# and opens the hub dashboard. Run from the repo root:  .\orchestration\apply_addendum.ps1
param(
    [string]$Python = "C:\Users\ethan\AppData\Local\Programs\Python\Python312\python.exe",
    [int]$GuiPort = 8766
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
function Hub { & $Python "$Root\communication_hub.py" --root "$Root" @args; if ($LASTEXITCODE) { throw "hub failed: $args" } }

$tasks = (Hub tasks) | ConvertFrom-Json
if ($tasks.PSObject.Properties.Name -contains "MM-VERCEL-API") { Write-Host "addendum already loaded" }
else { Hub plan "$Root\orchestration\plan_addendum_vercel_submission.json" }

Hub context-add kaggle-runbook "orchestration/KAGGLE_RUNBOOK.md" --description "Kaggle GPU run procedure; token is human-provisioned in ~/.kaggle, never read or committed"
Hub --agent human send gemini "MM-GPU-VALIDATION: Kaggle auth is provisioned in ~/.kaggle/access_token. Follow context source kaggle-runbook. Never read/print/commit the token." --type STATUS_UPDATE
Hub --agent human send all "Plan addendum loaded: MM-VERCEL-API (claude), MM-VERCEL-UI (gemini), MM-VERCEL-DEPLOY (codex, preview only), MM-SUBMISSION (claude, not gated on GPU). Streamlit stays local-only; Vercel uses api/ + public/." --type STATUS_UPDATE

if (-not (Test-Path "$Root\.gitignore") -or -not (Select-String -Path "$Root\.gitignore" -Pattern "^\.vercel" -Quiet)) { Add-Content "$Root\.gitignore" "`n.vercel/`n.env*`n" }

Hub metrics
Write-Host "Hub dashboard: http://127.0.0.1:$GuiPort/" -ForegroundColor Green
Hub gui --port $GuiPort
