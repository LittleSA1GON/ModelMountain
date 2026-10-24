# The Claude desktop app on this PC is the Microsoft Store (MSIX) build, which reads its MCP config from
# a virtualized folder, NOT %APPDATA%\Claude. This writes the ModelMountain hub (identity: claude) into
# every Claude config location that exists, with backups. Then fully quit Claude and reopen it.
$ErrorActionPreference = "Stop"
$Python = "C:\Users\ethan\AppData\Local\Programs\Python\Python312\python.exe"
$Root   = "E:\Software Engineering Stuff\Personal\ModelMountain"
$targets = @(
    (Join-Path $env:LOCALAPPDATA "Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json"),
    (Join-Path $env:APPDATA "Claude\claude_desktop_config.json")
)
$entry = [pscustomobject]@{
    command = $Python
    args    = @("$Root\communication_hub.py", "--root", $Root, "--agent", "claude", "mcp")
}
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
foreach ($cfg in $targets) {
    $dir = Split-Path $cfg
    if (-not (Test-Path $dir)) { Write-Host "skip (no folder): $dir"; continue }
    if (Test-Path $cfg) { Copy-Item $cfg "$cfg.bak-$stamp"; $json = Get-Content $cfg -Raw | ConvertFrom-Json }
    else { $json = [pscustomobject]@{} }
    if (-not ($json.PSObject.Properties.Name -contains "mcpServers")) { $json | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{}) }
    foreach ($name in @("research_swarm_ai", "swarm_modelmountain_16f864bf")) {
        if ($json.mcpServers.PSObject.Properties.Name -contains $name) { $json.mcpServers.$name = $entry }
        else { $json.mcpServers | Add-Member -NotePropertyName $name -NotePropertyValue $entry }
    }
    $json | ConvertTo-Json -Depth 20 | Set-Content $cfg -Encoding UTF8
    Write-Host "updated: $cfg" -ForegroundColor Green
}
Write-Host "Now fully quit Claude (tray icon -> Quit; check Task Manager has no Claude.exe) and reopen it." -ForegroundColor Yellow
