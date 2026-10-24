# Model Mountain - multi-agent orchestration bootstrap (SpartHill IBM 2026)
# Run from PowerShell:  cd "E:\Software Engineering Stuff\Personal\ModelMountain"; .\orchestration\bootstrap.ps1
# Safe to re-run: the plan is loaded only once.
param(
    [string]$Python = "C:\Users\ethan\AppData\Local\Programs\Python\Python312\python.exe",
    [int]$GuiPort = 8766,
    [switch]$ApplyHarnessConfig   # pass to write Codex / Antigravity / Claude desktop MCP configs
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
function Hub { & $Python "$Root\communication_hub.py" --root "$Root" @args; if ($LASTEXITCODE) { throw "hub failed: $args" } }

Write-Host "== 1. Working branch" -ForegroundColor Cyan
$branch = git rev-parse --abbrev-ref HEAD
if ($branch -eq "main") { git checkout -b hackathon/build } else { Write-Host "on $branch" }

Write-Host "== 2. Pool: 3 agents, 1 task each, 30M token budget, 1h leases" -ForegroundColor Cyan
Hub pool --agents 3 --per-agent 1 --tokens 30000000 --context-bytes 32000 --lease 3600

Write-Host "== 3. Task DAG" -ForegroundColor Cyan
$tasks = (Hub tasks) | ConvertFrom-Json
if ($tasks.PSObject.Properties.Name -contains "MM-00") { Write-Host "plan already loaded" }
else { Hub plan "$Root\orchestration\plan.json" }

Write-Host "== 4. Claude Code project MCP config (.mcp.json)" -ForegroundColor Cyan
Copy-Item "$Root\.ai\harnesses\claude.mcp.json" "$Root\.mcp.json" -Force

Write-Host "== 5. Codex / Antigravity harness config" -ForegroundColor Cyan
Hub configure
if ($ApplyHarnessConfig) { Hub configure --apply; Write-Host "Restart Codex and Antigravity so they load swarm_modelmountain_16f864bf" -ForegroundColor Yellow }
else { Write-Host "Preview only. Re-run with -ApplyHarnessConfig to write the configs (backups are made)." -ForegroundColor Yellow }

Write-Host "== 6. Status" -ForegroundColor Cyan
Hub metrics
Write-Host "Dashboard: http://127.0.0.1:$GuiPort/  (Ctrl+C to stop)" -ForegroundColor Green
Hub gui --port $GuiPort
