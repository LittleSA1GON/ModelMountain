"""Prepare this project's external-agent pool and reviewed build DAG. No model calls."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    "codex": {"capabilities": ["architecture", "integration", "review", "testing"], "role": "architect_integrator"},
    "claude": {"capabilities": ["implementation", "architecture", "security", "rag", "mia", "evaluation", "research", "frontend", "review", "testing"], "role": "opus_technical_lead"},
    "gemini": {"capabilities": ["mechanical"], "role": "mechanical_helper"},
}


def hub(*args):
    result = subprocess.run([sys.executable, str(ROOT / "communication_hub.py"), "--root", str(ROOT), *args],
                            check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(result.stdout)


def main():
    hub("init", "--objective", "Build and independently validate Model Mountain using Codex, Claude Code and Antigravity")
    hub("pool", "--agents", "3", "--per-agent", "1", "--lease", "900")
    for agent, profile in PROFILES.items():
        args = ["worker", agent, "--role", profile["role"]]
        for capability in profile["capabilities"]:
            args.extend(["--capability", capability])
        hub(*args)
    plan = json.loads((ROOT / "agent_workflow/build_plan.json").read_text(encoding="utf-8"))
    existing = set(hub("tasks"))
    expected = {task["id"] for task in plan["tasks"]}
    if expected & existing and not expected <= existing:
        raise SystemExit("Partial plan exists. Inspect it before changing the durable task graph.")
    if not expected <= existing:
        hub("plan", str(ROOT / "agent_workflow/build_plan.json"))
    for source_id, path in [("build-runbook", "agent_workflow/ORCHESTRATION.md"),
                            ("build-plan", "agent_workflow/build_plan.json"),
                            ("build-contracts", "agent_workflow/BUILD_CONTRACT.md"),
                            ("handoff", "MULTIAGENT_HANDOFF.md")]:
        hub("context-add", source_id, path, "--description", "Model Mountain approved build context")
    print(json.dumps({"prepared": True, "tasks": len(expected), "agents": list(PROFILES),
                      "mode": "external harnesses; no model sessions launched",
                      "client_configuration_modified": False}, indent=2))


if __name__ == "__main__":
    main()
