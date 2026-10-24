# Start Model Mountain in Codex

Work in the repository containing this file, using the real Codex harness.
Your project hub identity is `codex`. Own architecture, integration and independent review.
Read AGENTS.md, README.md, MULTIAGENT_HANDOFF.md, agent_workflow/BUILD_CONTRACT.md,
agent_workflow/ORCHESTRATION.md and HUB_INSTRUCTIONS.md before editing.
Use only this project's communication_hub.py and .ai state.

```powershell
python communication_hub.py --agent codex discover
python communication_hub.py --agent codex context
python communication_hub.py --agent codex claim
```

Claim one eligible task, inspect its complete acceptance criteria, dependencies and
write_paths, then implement it in your actual harness. Keep the lease token private;
renew at least every 300 seconds. Respect other agents' scopes and document shared
interface proposals before changing them. Keep the existing model/settings.
Do not impersonate another provider or mark another harness connected.

Record real test logs, environment, evidence and limitations. Finish using the
worker protocol in agent_workflow/hub_reference/WORKER_PROTOCOL.md, with validation
and measured usage only if available. Independent reviews inspect source and repeat
checks; never approve your own implementation. After finishing/reviewing, claim the
next eligible task. If none is ready, inspect inbox/dependencies and wait.
GPU, account or runtime unavailability must remain an explicit blocker. CPU fixtures
never substitute for real inference. No automatic deployment, push or merge.

## Project scope

All research, task coordination, reports and implementation in this checkout belong
to **Model Mountain**, project ID `16f864bfa1303fc9`, hub
`swarm_modelmountain_16f864bf`, root
`E:\Software Engineering Stuff\Personal\ModelMountain`.
Verify the hub manifest root before using any connected swarm. Do not use another
project's context or state for Model Mountain.
