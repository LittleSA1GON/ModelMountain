# Model Mountain orchestration

Prepared for Codex, Claude Code and Google Antigravity. `gemini` is the hub identity
for Antigravity; it does not assert a selected model. All agents retain their harness
model/settings. The archive's default model metadata is not an availability check.

The canonical root is the directory containing `communication_hub.py`. State lives
in its `.ai/` directory. Other connected project hubs must never be used for this build.
The portable hub runs with Python 3.11+; the application itself supports Python 3.10+.

## Prepared work

Source was restored from 57 notebook payloads through AST literal parsing, base64
and zlib; notebook cells were not executed. RESTORE_MANIFEST.json records original
payload hashes. The source tree is now canonical; a later release task must rebuild
and verify notebook payloads after source changes. The original notebook and hub ZIP
are preserved. The hub archive supplies `communication_hub.py` and its bundled runtime.

`build_plan.json` is the executable dependency graph. Every task needs passing
validation evidence and at least one independent reviewer; high-risk tasks require
two distinct peer reviewers. Capability routing fixes lane
ownership; reviewers use the shared `review` capability. The pool allows three
identities, one active task each. It retains the hub's default 100,000 estimated-token
guard as a first tranche, not an estimate for the full build or a provider billing cap.
External harnesses enforce their own usage limits; do not silently increase budgets.

| Participant | Build ownership |
|---|---|
| Codex (`codex`) | integration, security/correctness verification, deployment checks and independent review |
| Claude Opus 5.5 (`claude`) | majority technical leadership, security/RAG/MIA, evaluation, and fresh UI/design implementation |
| Antigravity (`gemini`) | explicitly assigned mechanical chores only; no technical/design/review authority |

Live communication confirmed on 2026-10-23 by nonce-correlated hub replies from
Claude Code Opus 5.5 and Antigravity Gemini 3.8 Flash (High). Opus now leads technical and creative implementation; Codex verifies correctness.
Earlier Flash implementation assignments are withdrawn by explicit user direction.
Critical reasoning and security decisions require Codex/Opus peer sign-off.
See BASELINE_STATUS.json for message references and KAGGLE.md for GPU staging.

MM-CONTRACTS and MM-PROTOCOL can begin together. Security, RAG and backends follow
the reviewed contract. The benchmark follows protocol, retrieval and backend work.
Dashboard follows benchmark and application boundary. CPU integration and GPU runtime
validation follow separately. The final task requires both, independent review and
notebook/packaging verification. See the task board for scopes and acceptance criteria.

## Start the prepared hub

From the repository root in PowerShell:

```powershell
python agent_workflow/setup_orchestration.py
python communication_hub.py metrics
python communication_hub.py gui --port 8776
```

The GUI is loopback-only at http://127.0.0.1:8776/. It shows durable tasks, leases,
messages and reviews; opening it does not launch any model sessions.
Setup is repeatable before active runs and preserves tasks/history. Drain active
runs before changing worker profiles. No global client settings are edited.

## Connect the actual harnesses

Open this repository in each actual harness and paste its file under `prompts/`:
`codex.md`, `claude-code.md`, or `antigravity.md`. Those prompts use the working
local CLI transport, so MCP installation is unnecessary. Launching another Codex
subagent is not a substitute for Claude Code or Antigravity.

Each harness reads AGENTS.md, its harness instructions, BUILD_CONTRACT.md and
HUB_INSTRUCTIONS.md. Run with its own identity:

```powershell
python communication_hub.py --agent claude discover
python communication_hub.py --agent claude context
python communication_hub.py --agent claude claim
```

Use `codex` or `gemini` in the other harnesses. A null claim means no eligible task
is ready; inspect dependencies/reviews and wait. Do not create a fake completion.
Claim responses contain private lease tokens. Keep them local and out of shared logs.
Renew before expiry (900-second lease; renew every 300 seconds or sooner):

```powershell
python communication_hub.py --agent claude renew-run RUN_ID LEASE_TOKEN
python communication_hub.py --agent claude finish-run RUN_ID LEASE_TOKEN --file .ai/claude-result.json
```

Confirm exact argument names with each command's `--help`. Use the worker result
schema in `hub_reference/WORKER_PROTOCOL.md`; evidence must point to real files/logs.
Reviews must inspect the implementation and repeat relevant checks under a different
identity. Never label estimated usage as measured provider usage. Report blockers via
`fail-run` and the inbox; do not retry unknown side effects without inspection.

The generated `.ai/harnesses/*.mcp.json` files are optional local connection templates,
not installed client settings or verified live connections. MCP activation is a separate
client setup step with the installed precheck workflow. CLI transport is ready now.

## File ownership and recovery

Task `write_paths` reserve canonical paths atomically; leases are coordination, not
an OS sandbox. This Git repository has no initial commit, so worktrees cannot yet be
created. Until a baseline commit is available, use the non-overlapping leased scopes
in the shared root and serialize cross-scope integration. Do not edit another active
scope. Once usable Git history exists, prefer project-local isolated worktrees; keep
the canonical `--root` for coordination. Do not share or copy `.ai/` to other projects.

After a crash, inspect the old process and edits, recover your run via `run-detail`,
and resolve retained leases before retrying. Never release another active agent's
lease or hand-edit the SQLite state. Do not merge, push or deploy from a build claim.

## Verification

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m model_mountain.evaluation --output model_mountain_results/reliability.json
.venv/Scripts/python.exe -m model_mountain.integrated_demo --output model_mountain_results/integrated_gateway.json
python agent_workflow/verify_orchestration.py
```

`BASELINE_STATUS.json` records the preparation checks. `.ai/` contains machine-local
inventory and the mutable board; neither belongs in a portable release.

## Project scope

All research, task coordination, reports and implementation in this checkout belong
to **Model Mountain**, project ID `16f864bfa1303fc9`, hub
`swarm_modelmountain_16f864bf`, root
`E:\Software Engineering Stuff\Personal\ModelMountain`.
Verify the hub manifest root before using any connected swarm. Do not use another
project's context or state for Model Mountain.

## Current allocation â€” user override, 2026-10-23

Claude Opus 5.5 leads the majority of technical implementation, architecture,
model/MIA work, evaluation design and all creative/UI design. Codex performs
integration, security/correctness checks and independent verification.
Antigravity is limited to explicitly assigned mundane, repetitive tasks with
exact steps (file inventories, prescribed test/build commands, formatting).
It must not design, implement production code, create datasets/protocols, choose
models/vectors, or approve technical work. Earlier conflicting allocations are
superseded. All work belongs only to Model Mountain, project 16f864bfa1303fc9.
