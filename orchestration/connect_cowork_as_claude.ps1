# Make Claude Cowork (desktop app) the `claude` identity on the ModelMountain hub.
# Run from the repo root:  .\orchestration\connect_cowork_as_claude.ps1   then FULLY quit and reopen the Claude desktop app.
param([string]$Python = "C:\Users\ethan\AppData\Local\Programs\Python\Python312\python.exe")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
function Hub { & $Python "$Root\communication_hub.py" --root "$Root" @args; if ($LASTEXITCODE) { throw "hub failed: $args" } }

# 1. Register swarm_modelmountain_16f864bf (identity=claude) in %APPDATA%\Claude\claude_desktop_config.json.
#    Also refreshes the Codex/Antigravity entries; the hub backs up every file it changes.
Hub configure --apply

# 2. Tell the swarm who operates `claude` now, so nobody double-claims.
Hub --agent human send all "Identity change: 'claude' is now operated by Claude Cowork (Claude desktop app, Opus 5.5, via device bridge), not the Claude Code CLI. The CLI session must stop claiming work. Codex/Antigravity: expect a fresh nonce handshake from claude after the desktop app restarts." --type STATUS_UPDATE

# 3. Load Vercel + submission tasks if not loaded yet (idempotent).
$tasks = (Hub tasks) | ConvertFrom-Json
if (-not ($tasks.PSObject.Properties.Name -contains "MM-VERCEL-API")) { Hub plan "$Root\orchestration\plan_addendum_vercel_submission.json" }

Write-Host "`nDone. Now: close the Claude Code CLI window, fully quit the Claude desktop app (tray icon -> Quit), reopen it, and tell Claude 'connected'." -ForegroundColor Green
