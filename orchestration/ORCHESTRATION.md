# Model Mountain: multi-agent build plan (SpartHill Hacks 2026, IBM AI Challenge)

**Event:** Oct 23–24, 2026, SJSU Spartan Complex. Judges score four equal criteria: Technical Execution, Innovation, Challenge Fit & Real-World Impact, and Feasibility & Implementation. The submission needs a public repo with a setup README, a demo (a video of 3 minutes or less, or a live link), the Devpost description questions, and an AI-use disclosure. It must contain no secrets. Organizers announce the final cutoff on site.

**Hub:** `communication_hub.py` (project-local, MCP server `swarm_modelmountain_16f864bf`). The state lives in `.ai/`. Never edit it by hand.

## Agents and routing

Tasks route by **capability**. Each task asks for capabilities that only one agent has, so the scheduler picks the right owner on its own. A different agent cross-reviews every result.

| Identity | Harness | Role | Owns |
|---|---|---|---|
| `claude` | Claude Code | implementation engineer | MM-00, 10, 11, 13, 22 |
| `codex` | OpenAI Codex | architect / evaluator / reviewer | MM-01, 12, 14, 20, 30 |
| `gemini` | Google Antigravity | research / browser QA / release | MM-02, 21, 31, 32 |

## Task DAG

```
MM-00 baseline ─┐
MM-01 contract ─┼─> MM-10 Granite backend ─> MM-11 pipeline ─┬─> MM-13 Live Demo tab ─> MM-21 QA ─> MM-22 fixes ─┐
MM-02 research ─┘                                            │                                                  ├─> MM-30 README+Devpost ─> MM-31 video script ─> MM-32 release gate
MM-01 ─────────────────────> MM-12 held-out benchmark ───────┴─> MM-20 run benchmark + RESULTS.md ───────────────┘
MM-00 ─> MM-14 (STRETCH) real IBM MIA GPU run on Kaggle
```

The three Wave 1 tasks run in parallel. Each agent holds one task at a time, and file leases (`write_paths`) block overlapping edits.

## Pitch strategy (why these tasks)

- **IBM fit:** live inference runs on a local **IBM Granite** model (MM-10), and the stretch goal is a real **IBM MIA** run (MM-14). The challenge doesn't require IBM tech, but using it helps the IBM judges see the fit.
- **Technical Execution:** a single end-to-end, fail-closed pipeline with an audit trail (MM-11), backed by tests and a held-out benchmark that reports confidence intervals (MM-12/20).
- **Innovation:** model-internal signals (MIA) sit beside external controls, and the demo compares protected and unprotected runs side by side (MM-13).
- **Responsible AI and impact:** honest evidence labels (CPU_SYNTHETIC vs LIVE), a NIST AI RMF / OWASP mapping (MM-02), and a limitations section.
- **Feasibility:** clean-clone QA (MM-21), a release gate (MM-32), and a next-steps roadmap.

## Gates

- Every task needs passing validation evidence and **1 independent review** from a different identity.
- Agents commit locally on `hackathon/build`. **Only the human merges, pushes, and submits to Devpost.**
- If a task fails, inspect it, then run `retry MM-XX --reason ...`.

## Start

1. `.\orchestration\bootstrap.ps1 -ApplyHarnessConfig`. This creates the branch, sizes the pool, loads the plan, writes `.mcp.json` for Claude Code, writes the Codex and Antigravity MCP configs (with backups), and opens the dashboard at :8766.
2. Restart Codex and Antigravity, then open Claude Code in the repo root and approve the project MCP server.
3. Paste each agent's prompt from `KICKOFF_PROMPTS.md`.
4. Watch the dashboard. Act as the tie-breaker reviewer and run the MM-14 Kaggle step yourself.
