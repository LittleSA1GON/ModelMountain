# Model Mountain build task board

The executable source of truth is `build_plan.json`; mutable status is in the local hub.
The original 11-task graph is historical. Current task state and replacement Opus tasks are in the local hub. Withdrawn Antigravity outputs are not accepted completion evidence.
See ORCHESTRATION.md for start commands and BUILD_CONTRACT.md for evidence requirements.

| Task | Lane | Dependencies | Scope |
|---|---|---|---|
| MM-CONTRACTS | architecture | none | Codex: freeze application and inference interfaces |
| MM-PROTOCOL | evaluation | none | Opus5.5 replacement: freeze held-out evaluation protocol |
| MM-SECURITY | security | MM-CONTRACTS | Claude Code: implement trusted application security boundary |
| MM-RAG | rag | MM-CONTRACTS | Claude Code: implement protected ingestion and retrieval |
| MM-BACKEND | mia | MM-CONTRACTS | Claude Code: integrate real model and opt-in MIA adapters |
| MM-EVALUATOR | evaluation | MM-PROTOCOL, MM-RAG, MM-BACKEND | Opus5.5 replacement: implement unified independent A/B/C/D evaluator |
| MM-APPLICATION | integration | MM-SECURITY, MM-RAG, MM-BACKEND | Codex: expose integrated local application workflow |
| MM-DASHBOARD | frontend | MM-APPLICATION, MM-EVALUATOR | Opus5.5 replacement: complete dashboard and evidence inspection |
| MM-CPU-INTEGRATION | integration | MM-APPLICATION, MM-EVALUATOR, MM-DASHBOARD | Codex: verify clean install, CI and notebook parity |
| MM-GPU-VALIDATION | research | MM-BACKEND, MM-EVALUATOR, MM-APPLICATION | Opus5.5 replacement: independently run pinned real inference trial |
| MM-RELEASE | integration | MM-CPU-INTEGRATION, MM-GPU-VALIDATION | Codex: assemble independently reviewed research workbench release |

Every task requires independent review and passing validation evidence; high-risk tasks require two distinct reviewers.
The final release waits for actual GPU validation; an explicit incompatibility remains a blocker.
File leases use each task policy, including separate test files to prevent overlapping edits.

## Current allocation â€” user override, 2026-10-23

Claude Opus 5.5 leads the majority of technical implementation, architecture,
model/MIA work, evaluation design and all creative/UI design. Codex performs
integration, security/correctness checks and independent verification.
Antigravity is limited to explicitly assigned mundane, repetitive tasks with
exact steps (file inventories, prescribed test/build commands, formatting).
It must not design, implement production code, create datasets/protocols, choose
models/vectors, or approve technical work. Earlier conflicting allocations are
superseded. All work belongs only to Model Mountain, project 16f864bfa1303fc9.
