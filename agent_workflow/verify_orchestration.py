"""Exercise the real build DAG in disposable state without contacting providers."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from setup_orchestration import PROFILES, ROOT


def main():
    with tempfile.TemporaryDirectory(prefix="model-mountain-hub-") as directory:
        def hub(*args, agent=None):
            command = [sys.executable, str(ROOT / "communication_hub.py"), "--root", directory]
            if agent:
                command += ["--agent", agent]
            p = subprocess.run(command + list(args), capture_output=True, text=True, encoding="utf-8", check=True)
            return json.loads(p.stdout)

        hub("init", "--no-onboard")
        for agent, profile in PROFILES.items():
            args = ["worker", agent]
            for capability in profile["capabilities"]:
                args += ["--capability", capability]
            hub(*args)
        hub("plan", str(ROOT / "agent_workflow/build_plan.json"))
        codex = hub("claim", agent="codex")
        gemini = hub("claim", agent="gemini")
        assert codex["task_id"] == "MM-CONTRACTS", codex
        assert gemini["task_id"] == "MM-PROTOCOL", gemini
        assert hub("claim", agent="claude") is None, "Dependencies must prevent premature implementation"
        result = Path(directory) / "result.json"
        result.write_text(json.dumps({"summary": "Offline scheduler contract fixture only",
                                     "evidence": ["Disposable fixture; no model or product claim"],
                                     "validation": {"passed": True, "evidence": ["Fixture validation"]},
                                     "usage": {"input_tokens": 0, "output_tokens": 0}}), encoding="utf-8")
        hub("finish-run", codex["id"], codex["lease_token"], "--file", str(result), agent="codex")
        tasks = hub("tasks")
        assert tasks["MM-CONTRACTS"]["status"] != "completed", "Independent review must gate dependencies"
        assert hub("claim", agent="codex") is None, "Implementer must not self-review"
        review = hub("claim", agent="claude")
        assert review["context"]["review_target"]["task_id"] == "MM-CONTRACTS"
        assert review["context"]["review_target"]["implementer"] == "codex"
        plan = json.loads((ROOT / "agent_workflow/build_plan.json").read_text(encoding="utf-8"))
        print(json.dumps({"passed": True, "task_count": len(plan["tasks"]),
                          "checks": ["actual plan loads", "capability ownership", "parallel first tasks",
                                     "dependency gating", "completion waits for review", "self-review excluded",
                                     "independent reviewer receives evidence"],
                          "scope": "Disposable scheduler test; actual provider sessions unverified"}, indent=2))


if __name__ == "__main__":
    main()
