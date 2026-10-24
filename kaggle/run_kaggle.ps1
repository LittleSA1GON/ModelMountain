# Model Mountain v2: run the emotion-vector study on private Kaggle GPU kernels (owner's PC; Kaggle CLI >= 1.8).
#   .\kaggle\run_kaggle.ps1 -Owner littlesa1gon                       # stories kernel, then every model below in turn
#   .\kaggle\run_kaggle.ps1 -Owner littlesa1gon -SkipStories -Models "google/gemma-4-E2B-it"
#   .\kaggle\run_kaggle.ps1 -Owner littlesa1gon -PreflightOnly
# Auth: Kaggle CLI reads %USERPROFILE%\.kaggle\access_token. This script never reads or prints it.
# Kernels run one at a time (Kaggle GPU concurrency + weekly quota). Each model kernel is ~1-2.5 GPU hours.
param(
    [Parameter(Mandatory = $true)][string]$Owner,
    [string[]]$Models = @(
        "Qwen/Qwen2.5-1.5B-Instruct", "ibm-granite/granite-3.1-2b-instruct", "ibm-granite/granite-4.0-micro",
        "google/gemma-4-E2B-it", "Qwen/Qwen2.5-3B-Instruct", "Qwen/Qwen2-1.5B-Instruct",
        "Qwen/Qwen2.5-7B-Instruct", "ibm-granite/granite-3.1-8b-instruct", "google/gemma-4-E4B-it"),
    [string]$Generator = "Qwen/Qwen2.5-7B-Instruct",
    [string]$Python = ".venv\Scripts\python.exe",
    [int]$PollSeconds = 90,
    [int]$MaxMinutes = 540,
    [switch]$SkipStories,
    [switch]$PreflightOnly
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

& $Python -m pip install -q "kaggle>=1.8" huggingface_hub | Out-Null
kaggle kernels list --mine --page-size 1 | Out-Null
if ($LASTEXITCODE) { throw "Kaggle auth failed (check ~/.kaggle/access_token). Report as BLOCKER; do not retry with other credentials." }
if (-not (Test-Path "kaggle\model_allowlist.json")) { & $Python kaggle\resolve_revisions.py; if ($LASTEXITCODE) { throw "revision resolution failed" } }
$allow = Get-Content "kaggle\model_allowlist.json" -Raw

function Run-Kernel([string[]]$BuildArgs, [string]$Label) {
    $bundle = (& $Python kaggle\build_kernel.py --owner $Owner @BuildArgs | Select-Object -Last 1).Trim()
    if ($LASTEXITCODE) { Write-Warning "build failed for $Label"; return "build_failed" }
    $ref = (Get-Content "$bundle\kernel-metadata.json" -Raw | ConvertFrom-Json).id
    Write-Host "[$Label] push $ref ($bundle)" -ForegroundColor Cyan
    kaggle kernels push -p $bundle
    if ($LASTEXITCODE) { Write-Warning "push failed for $Label"; return "push_failed" }
    $deadline = (Get-Date).AddMinutes($MaxMinutes)
    do {
        Start-Sleep -Seconds $PollSeconds
        $status = (kaggle kernels status $ref) -join " "
        Write-Host (Get-Date -Format "HH:mm:ss") "[$Label]" $status
    } while ($status -match "running|queued" -and (Get-Date) -lt $deadline)
    $dest = "model_mountain_results\kaggle\" + (Split-Path $bundle -Leaf)
    New-Item -ItemType Directory -Force $dest | Out-Null
    kaggle kernels output $ref -p $dest
    $status | Out-File "$dest\kernel_status.txt"
    Write-Host "[$Label] outputs in $dest" -ForegroundColor Green
    return $status
}

if ($PreflightOnly) { Run-Kernel @("--preflight-only") "preflight" | Out-Null; return }

$log = @()
if (-not $SkipStories) {
    $s = Run-Kernel @("--stories", "--generator", $Generator) "stories"
    $log += [pscustomobject]@{ kernel = "stories"; status = $s }
    if ($s -notmatch "complete") { $log | Format-Table; throw "stories kernel did not complete; model kernels need stories.json" }
}
foreach ($m in $Models) {
    if ($allow -notmatch [regex]::Escape("`"$m`"")) { Write-Warning "$m not pinned in model_allowlist.json; skipped"; $log += [pscustomobject]@{ kernel = $m; status = "not_pinned" }; continue }
    $s = Run-Kernel @("--model", $m) $m
    $log += [pscustomobject]@{ kernel = $m; status = $s }
}
$log | Format-Table -AutoSize
$log | ConvertTo-Json | Out-File "model_mountain_results\kaggle\run_log_$(Get-Date -Format yyyyMMddTHHmmss).json"
