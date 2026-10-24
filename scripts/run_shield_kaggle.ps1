# Model Mountain: run the protection-steering ("injection shield") kernel on Kaggle and ingest the result.
# Run from PowerShell in the repo root (Kaggle CLI uses %USERPROFILE%\.kaggle\access_token; never read or printed):
#   powershell -ExecutionPolicy Bypass -File .\scripts\run_shield_kaggle.ps1
# One private GPU kernel (T4 x2, internet on) fits and tests the shield for Qwen2.5-1.5B, Granite-3.1-2B and
# Gemma-4-E4B in turn (~40-60 min). Outputs land in model_mountain_results\kaggle\shield-v1\, then
# api\experiments.json and docs\RESULTS.md are regenerated. Afterwards run scripts\finish_submission.ps1 again.
param(
    [string]$Owner = "littlesa1gon",
    [int]$PollSeconds = 60,
    [int]$MaxMinutes = 110
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
function Check($what) { if ($LASTEXITCODE) { throw "$what failed (exit $LASTEXITCODE)" } }

kaggle kernels list --mine --page-size 1 | Out-Null
if ($LASTEXITCODE) { throw "Kaggle CLI auth failed (check %USERPROFILE%\.kaggle\access_token)" }

$bundle = (& $Py kaggle\build_kernel.py --owner $Owner --shield | Select-Object -Last 1).Trim(); Check "kernel build"
$ref = (Get-Content "$bundle\kernel-metadata.json" -Raw | ConvertFrom-Json).id
Write-Host "Pushing $ref from $bundle" -ForegroundColor Cyan
kaggle kernels push -p $bundle; Check "kaggle kernels push"

$deadline = (Get-Date).AddMinutes($MaxMinutes)
do {
    Start-Sleep -Seconds $PollSeconds
    $status = (kaggle kernels status $ref) -join " "
    Write-Host (Get-Date -Format "HH:mm:ss") $status
} while ($status -match "running|queued" -and (Get-Date) -lt $deadline)

$dest = "model_mountain_results\kaggle\shield-v1"
New-Item -ItemType Directory -Force $dest | Out-Null
kaggle kernels output $ref -p $dest; Check "kaggle kernels output"
$status | Out-File "$dest\kernel_status.txt"
$res = if (Test-Path "$dest\mm_results\summary.json") { "$dest\mm_results" } else { $dest }
if (-not (Test-Path "$res\summary.json")) { throw "No summary.json in $dest; see the kernel log there" }

$K = "model_mountain_results\kaggle"
& $Py scripts\ingest_kaggle_results.py "$K\stories-v2\mm_results" "$K\qwen-v4\mm_results" "$K\granite-v1\mm_results" "$K\gemma-e4b-v1\mm_results" `
    --heads-from "$K\attention-review-v1\mm_results" --shield-from $res; Check "ingest"
& $Py scripts\build_results_md.py; Check "RESULTS.md"
$lines = @(Select-String -Path docs\RESULTS.md -Pattern "Protection steering")
Write-Host "Shield results in docs\RESULTS.md: $($lines.Count) model(s)"
Write-Host "`nNext: powershell -ExecutionPolicy Bypass -File .\scripts\finish_submission.ps1 -SkipTests" -ForegroundColor Green
