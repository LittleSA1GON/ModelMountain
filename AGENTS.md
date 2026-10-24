# Model Mountain — Instructions for Coding Agents

This is the **Model Mountain** v4 codebase, formerly named IceWall. All executable code and documentation must use the `model_mountain` Python package and the `Model Mountain` project name. Do not reintroduce `icewall` imports.

## Non-negotiable evidence rules

- Never label deterministic CPU fixtures or synthetic activation vectors as real LLM security or factuality results.
- Never claim steering prevents attacks, reduces hallucinations, or improves production safety without independent held-out real-model outcomes.
- Keep authorization, tenant boundaries, MCP trust verification, and action approval **outside** the model, even if steering is enabled.
- Handle activation captures, documents, tokens, API secrets, and model outputs as potentially sensitive information. Never commit live secrets or unredacted enterprise data.
- Preserve model/layer binding, artifact integrity, held-out split separation, provenance fields, and conservative failure behavior.

## First steps

1. Read `README.md`, `MULTIAGENT_HANDOFF.md`, `BEHAVIORAL_VECTOR_LAB.md`, and `agent_workflow/TASK_BOARD.md`.
2. Install local CPU deps: `python -m pip install -e .` (add `.[vector-lab]` for vector fitting tests, if Torch is not already installed).
3. Run `python -m unittest discover -s tests -v` from the repository root.
4. Run `python -m model_mountain.evaluation --output model_mountain_results/reliability.json`.
5. Use `python -m model_mountain.integrated_demo --output model_mountain_results/integrated_gateway.json` for the synthetic security demo.

## Coordination

Work is split into non-overlapping scopes in `agent_workflow/TASK_BOARD.md`. Prefer isolated branches/worktrees per agent; declare shared interface changes before editing another agent's files. Run tests before proposing changes, keep experiments opt-in and labeled, and add tests for behavior changes.

**No GPU claims are established by this source distribution.** IBM vLLM-Hook/MIA capture and steering require a compatible dedicated GPU runtime, an installed/pinned IBM environment, and independent evaluation.

<!-- SWARM-HUB:START -->
Read [HUB_INSTRUCTIONS.md](HUB_INSTRUCTIONS.md) for this project's multi-agent orchestration and completion protocol.
<!-- SWARM-HUB:END -->

## Project scope

All research, task coordination, reports and implementation in this checkout belong
to **Model Mountain**, project ID `16f864bfa1303fc9`, hub
`swarm_modelmountain_16f864bf`, root
`E:\Software Engineering Stuff\Personal\ModelMountain`.
Verify the hub manifest root before using any connected swarm. Do not use another
project's context or state for Model Mountain.

## Current allocation — user override, 2026-10-23

Claude Opus 5.5 leads the majority of technical implementation, architecture,
model/MIA work, evaluation design and all creative/UI design. Codex performs
integration, security/correctness checks and independent verification.
Antigravity is limited to explicitly assigned mundane, repetitive tasks with
exact steps (file inventories, prescribed test/build commands, formatting).
It must not design, implement production code, create datasets/protocols, choose
models/vectors, or approve technical work. Earlier conflicting allocations are
superseded. All work belongs only to Model Mountain, project 16f864bfa1303fc9.
