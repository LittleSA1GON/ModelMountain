# Multi-agent workflow

The ZIP is a portable repo handoff for a coding-agent environment (Codex, Claude Code, etc.); it does not require a specific orchestration framework.

1. Extract ZIP and `cd Model_Mountain`.
2. Give every agent `AGENTS.md` and `MULTIAGENT_HANDOFF.md` as shared context.
3. Give each specialized agent exactly one `agent_workflow/roles/*.md` brief, and assign separate branches or worktrees.
4. Use `TASK_BOARD.md` as the canonical task backlog. Agents should post API-contract proposals before shared interfaces are changed.
5. The integrator merges only tested work and produces an evidence report; do not conflate local simulation tests with real-model/GPU validation.

Suggested kickoff: **security agent + RAG agent + MIA agent + evaluator**, with an integrator coordinating integration and documentation. Avoid parallel editing of `model_mountain/gateway.py` and `app.py` without coordination.
