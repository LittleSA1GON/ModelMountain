# Model Mountain: run the Try-it gateway scenarios on a real GPU model (Qwen2.5-1.5B + IBM MIA) and ingest them.
# Run from PowerShell in the repo root (Kaggle CLI uses %USERPROFILE%\.kaggle\access_token; never read or printed):
#   powershell -ExecutionPolicy Bypass -File .\scripts\run_tryit_kaggle.ps1
# One private GPU kernel (~12-15 min): real Qwen replies for every gateway scenario, with and without Model Mountain,
# plus the MIA Attention Tracker focus score per prompt. Outputs land in model_mountain_results\kaggle\tryit-v1\.
param(
    [string]$Owner = "littlesa1gon",
    [int]$PollSeconds = 60,
    [int]$MaxMinutes = 60,
    [string]$Ref = ""          # resume an already-pushed kernel, e.g. littlesa1gon/model-mountain-tryit
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
function Check($what) { if ($LASTEXITCODE) { throw "$what failed (exit $LASTEXITCODE)" } }

# Find (or install) the Kaggle CLI next to this Python; it is often not on PATH.
$Kaggle = $null
$cmd = Get-Command kaggle -ErrorAction SilentlyContinue
if ($cmd) { $Kaggle = $cmd.Source }
if (-not $Kaggle) {
    & $Py -m pip install -q "kaggle>=1.8" | Out-Null
    $dirs = @(& $Py -c "import sysconfig, os; print(sysconfig.get_path('scripts')); print(sysconfig.get_path('scripts', os.name + '_user'))")
    foreach ($d in $dirs) { $c = Join-Path $d.Trim() "kaggle.exe"; if (Test-Path $c) { $Kaggle = $c; break } }
}
if (-not $Kaggle) { throw "Kaggle CLI not found after install; run: $Py -m pip install kaggle  and check its Scripts folder" }
Write-Host "Using Kaggle CLI: $Kaggle"
& $Kaggle kernels list --mine --page-size 1 | Out-Null
if ($LASTEXITCODE) { throw "Kaggle CLI auth failed (check %USERPROFILE%\.kaggle\access_token)" }

if ($Ref) {
    $ref = $Ref
    Write-Host "Resuming $ref (no new push)" -ForegroundColor Cyan
} else {
    $bundle = (& $Py kaggle\build_kernel.py --owner $Owner --tryit | Select-Object -Last 1).Trim(); Check "kernel build"
    $ref = (Get-Content "$bundle\kernel-metadata.json" -Raw | ConvertFrom-Json).id
    Write-Host "Pushing $ref from $bundle" -ForegroundColor Cyan
    & $Kaggle kernels push -p $bundle; Check "kaggle kernels push"
}

$deadline = (Get-Date).AddMinutes($MaxMinutes)
do {
    Start-Sleep -Seconds $PollSeconds
    $status = (& $Kaggle kernels status $ref) -join " "
    Write-Host (Get-Date -Format "HH:mm:ss") $status
    if (-not $status -or $status -match "404|not found") { throw "Kaggle cannot find $ref; run again with -Ref <owner/slug> as shown on kaggle.com/code" }
} while ($status -match "running|queued" -and (Get-Date) -lt $deadline)
if ($status -match "error|cancel") { Write-Warning "Kernel ended with: $status (log is downloaded below)" }

$dest = "model_mountain_results\kaggle\tryit-v1"
New-Item -ItemType Directory -Force $dest | Out-Null
& $Kaggle kernels output $ref -p $dest; Check "kaggle kernels output"
$status | Out-File "$dest\kernel_status.txt"
$res = if (Test-Path "$dest\mm_results\summary.json") { "$dest\mm_results" } else { $dest }
if (-not (Test-Path "$res\summary.json")) { throw "No summary.json in $dest; see the kernel log there" }

$K = "model_mountain_results\kaggle"
$ingestArgs = @("$K\stories-v2\mm_results", "$K\qwen-v4\mm_results", "$K\granite-v1\mm_results", "$K\gemma-e4b-v1\mm_results",
          "--heads-from", "$K\attention-review-v1\mm_results", "--tryit-from", $res)
$shield = if (Test-Path "$K\shield-v1\mm_results\summary.json") { "$K\shield-v1\mm_results" } elseif (Test-Path "$K\shield-v1\summary.json") { "$K\shield-v1" } else { $null }
if ($shield) { $ingestArgs += @("--shield-from", $shield) }
& $Py scripts\ingest_kaggle_results.py @ingestArgs; Check "ingest"
& $Py scripts\build_results_md.py; Check "RESULTS.md"
Write-Host "`nNext: powershell -ExecutionPolicy Bypass -File .\scripts\finish_submission.ps1 -SkipTests" -ForegroundColor Green
