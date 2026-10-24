# Model Mountain: finish the submission from the owner's PC (replaces the Codex steps).
# Run from PowerShell in the repo root:
#   powershell -ExecutionPolicy Bypass -File .\scripts\finish_submission.ps1
# Steps: remove Build team leftovers -> tests + web build -> secret check -> commit -> push to GitHub
#        -> deploy to Vercel (production) -> verify the live site.
# It never reads or prints .env.local, Kaggle or Vercel credentials.
param(
    [string]$Message = "Model Mountain: protection steering (injection shield), web-search exfiltration guard, FP32 attention heads, Gemma results",
    [string]$Site = "https://model-mountain.vercel.app",
    [switch]$SkipTests,
    [switch]$SkipDeploy
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
function Step($n, $t) { Write-Host "`n[$n] $t" -ForegroundColor Cyan }
function Check($what) { if ($LASTEXITCODE) { throw "$what failed (exit $LASTEXITCODE)" } }

Step "1/7" "Remove Build team leftovers"
foreach ($f in @("web/src/views/Team.jsx", "api/orchestration_snapshot.json")) {
    if (Test-Path $f) { git rm -q --cached --ignore-unmatch $f | Out-Null; Remove-Item $f -Force; Write-Host "  removed $f" }
}
Get-ChildItem "docs/screenshots/web-v2" -Filter "team-*.png" -ErrorAction SilentlyContinue | ForEach-Object {
    git rm -q --cached --ignore-unmatch $_.FullName | Out-Null; Remove-Item $_.FullName -Force; Write-Host "  removed $($_.Name)"
}

if (-not $SkipTests) {
    Step "2/7" "Python tests"
    & $Py -m unittest discover -s tests -q; Check "Python tests"
    Step "3/7" "Web build and tests"
    Push-Location web
    try { npm ci; Check "npm ci"; npm run build; Check "web build"; npm test; Check "web tests" } finally { Pop-Location }
}

Step "4/7" "Secret check (file names and token patterns)"
git add -A; Check "git add"
$staged = @(git diff --cached --name-only)
$badNames = $staged | Where-Object { $_ -match '(^|/)\.env|access_token|(^|/)\.kaggle/|(^|/)\.vercel/|\.safetensors$|\.pt$|\.zip$|^gemma-4-' }
if ($badNames) { git reset -q; throw "Refusing to commit credential/model files: $($badNames -join ', ')" }
$tracked = @(git ls-files)
$badTracked = $tracked | Where-Object { $_ -match '(^|/)\.env(\.|$)|access_token' }
if ($badTracked) { git reset -q; throw "Credential files are tracked: $($badTracked -join ', ') - remove them from git first" }
$hits = git diff --cached -U0 | Select-String -Pattern 'KGAT_[A-Za-z0-9_-]{16,}', 'hf_[A-Za-z0-9]{30,}', 'ghp_[A-Za-z0-9]{30,}', 'github_pat_[A-Za-z0-9_]{30,}', 'sk-[A-Za-z0-9]{30,}', 'vercel_[A-Za-z0-9]{20,}'
if ($hits) { git reset -q; throw "Possible secret in staged changes ($(@($hits).Count) matching lines, not printed); nothing was committed" }
Write-Host "  $($staged.Count) staged files, no credential files or token patterns found"

Step "5/7" "Commit and push to GitHub"
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { Write-Host "  nothing new to commit" } else { git commit -q -m $Message; Check "git commit" }
$remotes = @(git remote)
if (-not ($remotes -contains "origin")) { git remote add origin https://github.com/LittleSA1GON/ModelMountain.git; Check "git remote add" }
git push -u origin main; Check "git push"
Write-Host "  pushed $(git rev-parse --short HEAD) to origin/main" -ForegroundColor Green

if (-not $SkipDeploy) {
    Step "6/7" "Deploy to Vercel (production)"
    vercel --prod --yes; Check "vercel deploy"
    Step "7/7" "Verify the live site"
    Start-Sleep -Seconds 10
    & $Py scripts\verify_deployment.py $Site; Check "deployment verification"
}
Write-Host "`nDone. Open $Site and https://github.com/LittleSA1GON/ModelMountain to check." -ForegroundColor Green
