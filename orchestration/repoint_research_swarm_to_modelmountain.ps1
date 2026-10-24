# Point the Claude desktop app's "research_swarm_ai" MCP server at the ModelMountain hub
# (identity: claude). Backs up the config first. Afterwards fully quit + reopen Claude.
# Effect: Cowork's "research swarm" tools operate on E:\...\Personal\ModelMountain\.ai,
# NOT the AI Research project. The AI Research hub itself is untouched on disk.
$ErrorActionPreference = "Stop"
$Python = "C:\Users\ethan\AppData\Local\Programs\Python\Python312\python.exe"
$Root   = "E:\Software Engineering Stuff\Personal\ModelMountain"
$Cfg    = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
if (-not (Test-Path $Cfg)) { throw "Claude desktop config not found at $Cfg" }

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item $Cfg "$Cfg.bak-$stamp"
$json = Get-Content $Cfg -Raw | ConvertFrom-Json
if (-not $json.mcpServers) { $json | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{}) }

$entry = [pscustomobject]@{
    command = $Python
    args    = @("$Root\communication_hub.py", "--root", $Root, "--agent", "claude", "mcp")
}
foreach ($name in @("research_swarm_ai", "swarm_modelmountain_16f864bf")) {
    if ($json.mcpServers.PSObject.Properties.Name -contains $name) { $json.mcpServers.$name = $entry }
    else { $json.mcpServers | Add-Member -NotePropertyName $name -NotePropertyValue $entry }
}
$json | ConvertTo-Json -Depth 20 | Set-Content $Cfg -Encoding UTF8
Write-Host "research_swarm_ai and swarm_modelmountain_16f864bf now both point to the ModelMountain hub." -ForegroundColor Green
Write-Host "Backup: $Cfg.bak-$stamp"

# Tell the ModelMountain swarm (recorded as human, since you are running it).
& $Python "$Root\communication_hub.py" --root $Root --agent human send all "Human: Cowork's research_swarm_ai MCP connection now points to the ModelMountain hub (not AI Research). All three harnesses work ONLY on ModelMountain via swarm_modelmountain_16f864bf / communication_hub.py in E:\Software Engineering Stuff\Personal\ModelMountain. Same three goals apply to all: (1) Kaggle multi-model vLLM-Hook MIA + emotion/activation vectors, (2) Vercel hackathon UI, (3) realistic security/robustness tests." --type STATUS_UPDATE

Write-Host "Now fully quit Claude (tray icon -> Quit) and reopen it, then tell Claude 'restarted'." -ForegroundColor Yellow
