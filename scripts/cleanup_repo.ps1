# Model Mountain: remove superseded files from the repository (run once, from the repo root).
#   powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_repo.ps1
# Deletes dead code, the old v4 dashboard/workers, emotion-study leftovers and stale notes.
# Multi-agent tooling (hub, agent instructions) is only untracked: it stays on disk for local use.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$delete = @(
    # stale root notes and the old v4 dashboard / GPU workers
    "BEHAVIORAL_VECTOR_LAB.md", "CYBERSECURITY_RISKS_AND_MIA.md", "DEVPOST_PITCH.md", "MCP_SECURITY_RESEARCH.md",
    "MIA_GATEWAY_IMPLEMENTATION.md", "MODEL_MOUNTAIN_IMPLEMENTATION_STATUS.md", "MULTIAGENT_HANDOFF.md",
    "RELEASE_NOTES_v3.md", "RELEASE_NOTES_v4.md", "Model_Mountain_Kaggle.ipynb", "app.py",
    "mia_behavior_capture_worker.py", "mia_behavior_eval_worker.py", "mia_gateway_worker.py", "mia_reliability_worker.py",
    "mia_rerank_worker.py", "mia_security_worker.py", "mia_steering_experiment_worker.py", "steerability360_worker.py",
    # modules nothing in the product imports any more
    "model_mountain/behavior_eval.py", "model_mountain/behaviorlab.py", "model_mountain/benchmark_metrics.py",
    "model_mountain/cli.py", "model_mountain/evaluation.py", "model_mountain/integrated_demo.py",
    "model_mountain/real_inputs.py", "model_mountain/reliability_demo.py", "model_mountain/risk_catalog.py",
    "model_mountain/steering.py", "tests/test_behaviorlab.py", "tests/test_benchmark_metrics.py",
    # unused fixtures, helper scripts and old docs
    "examples/behavior_abstention.json", "examples/behavior_grounding.json", "examples/behavior_injection_resistance.json",
    "examples/contrastive_prompts.json", "examples/heldout_security_reliability.json", "examples/steering_profile.template.json",
    "scripts/serve_submission_artifact.py", "kaggle/run_kaggle.ps1",
    "docs/CREDENTIALS.md", "docs/INTEGRATION_TESTING.md", "docs/SOFTWARE_TOOLKIT.md", "docs/FREE_TOOLS.md",
    "docs/screenshots", "docs/build/deployment", "docs/build/remote", "docs/build/hackathon", "docs/build/contracts/README.md"
)
foreach ($p in $delete) {
    if (Test-Path $p) {
        git rm -r -f -q --ignore-unmatch -- $p | Out-Null
        if (Test-Path $p) { Remove-Item -Recurse -Force $p }
        Write-Host "  deleted $p"
    }
}

$untrack = @("AGENTS.md", "CLAUDE.md", "GEMINI.md", "HUB_INSTRUCTIONS.md", "communication_hub.py", "agent_workflow", "orchestration")
foreach ($p in $untrack) { git rm -r -q --cached --ignore-unmatch -- $p | Out-Null }
$ignore = Get-Content .gitignore -Raw
if ($ignore -notmatch "communication_hub.py") {
    Add-Content .gitignore "`n# multi-agent tooling (kept locally, not part of the product)`nAGENTS.md`nCLAUDE.md`nGEMINI.md`nHUB_INSTRUCTIONS.md`ncommunication_hub.py`nagent_workflow/`norchestration/"
}
Write-Host "Cleanup done. Next: powershell -ExecutionPolicy Bypass -File .\scripts\finish_submission.ps1" -ForegroundColor Green
