# Model Mountain

**A security gateway for company AI assistants.** Five checks stop prompt injection, poisoned knowledge, data exfiltration through tools and links, malicious tool updates and model copying. IBM vLLM-Hook (MIA) adds model-internal defenses: an injection shield that steers models away from complying with injected instructions, Attention Tracker detector heads, and a hidden-state activation monitor.

SpartHill Hacks 2026 · IBM AI Challenge · **Live demo: https://model-mountain.vercel.app** · Results: [docs/RESULTS.md](docs/RESULTS.md)

## Why

Assistants that read email, documents and web pages and can call tools can be redirected by the text they read. Documented cases include EchoLeak (CVE-2025-32711), web-search-tool exfiltration (Rall et al., arXiv 2510.09093), Invariant Labs' MCP tool-poisoning and GitHub MCP reports, PromptArmor's Slack AI report, the malicious `postmark-mcp` package, CamoLeak, PoisonedRAG, and distillation campaigns reported by Anthropic (Feb 2026). The cited list is in `model_mountain/defenses.py` (`INCIDENTS`) and on the Defenses page.

## The five defenses

| # | Defense | What it stops | Code |
|---|---|---|---|
| 1 | Prompt-injection firewall + MIA Attention Tracker | Untrusted text acting as instructions | `core.py`, `gateway.py`, `kaggle/run_mia_kaggle.py:phase_heads` |
| 2 | RAG integrity and access control | Tampered or poisoned passages, cross-tenant retrieval | `rag.py`, `core.py` |
| 3 | Exfiltration guard | Auto-loaded images, data-carrying links, unapproved recipients, private-to-public flows, the "lethal trifecta", secrets sent through the agent's own web search/fetch tool, hidden text on retrieved pages | `egress.py` |
| 4 | MCP supply-chain guard | Poisoned tool descriptions, rug-pull updates, impersonated servers | `mcp_security.py` |
| 5 | Model-extraction guard | Output harvesting, including coordinated multi-account campaigns | `extraction.py` |

Every request runs through `ModelMountainGateway.evaluate`, which returns a per-stage trace of what each check decided.

## MIA defenses (IBM vLLM-Hook, Kaggle 2× T4)

Models: Qwen2.5-1.5B-Instruct, IBM Granite-3.1-2B-Instruct, Gemma-4-E4B-it, at pinned revisions.

| Defense | MIA worker | Method |
|---|---|---|
| Injection shield | `capture_hs` → `steer` (`add_vector`) | Direction = mean hidden state on Tensor Trust attacks that hijacked the model minus attacks it resisted; the shield steers against it. Strength chosen on validation attacks; measured on held-out attacks from unseen defenders, with legitimate-access and TruthfulQA side effects. `kaggle/run_mia_kaggle.py:phase_shield` |
| Attention Tracker detector | `capture_qk` + attention analyzer | Heads whose attention to the system instruction drops under injection (Hung et al., NAACL 2025 Findings); selected on training groups, scored on held-out groups. Captured fp16 Q/K analyzed in FP32 on the T4. Detector only, never steered. |
| Activation monitor | `capture_hs` (last token) | Linear probe trained on deepset prompt injections, reported with its false-positive rate on Tensor Trust. |

The Steering page opens models 1–3 with the injection-shield preset. Each profile is opt-in and bound to the vector file's SHA-256. It never replaces the five external checks.

### Measured so far

- **Attention Tracker heads:** Qwen 24 heads, Granite 64 heads, each with held-out AUROC 1.0 on a small labeled set (30 attacks, 5 benign; exploratory). Gemma 4's capture failed on the T4 because its layers mix attention geometries; the kernel now patches IBM MIA to capture uniform layers.
- **Activation monitor:** deepset test AUROC 0.98 (Qwen), but it flagged every Tensor Trust prompt including legitimate ones, so it is a monitor, not a gate.
- **Injection shield:** results appear in docs/RESULTS.md and the app once the shield kernel is ingested; until then the app shows "GPU run pending".

## Run it

```bash
python -m pip install -e .
python -m unittest discover -s tests
cd web && npm ci && npm run build && cd ..
python scripts/serve_web.py          # http://127.0.0.1:8502 (UI + /api/v1)
```

GPU (Kaggle, owner's PC): `scripts/run_shield_kaggle.ps1` runs the injection-shield kernel and ingests it; `python kaggle/build_kernel.py --owner <user> --model <id>` builds a full model kernel. Ingest with `scripts/ingest_kaggle_results.py`, then `scripts/build_results_md.py`. Deploy: `scripts/finish_submission.ps1`.

## Limits

- The live site runs the rule engine on CPU with inert fixtures; it never runs a model, executes a tool or sends data. Results are labeled `CPU_SYNTHETIC` or `REAL_IBM_MIA`.
- GPU results use small models and small held-out sets; intervals are wide and null results are reported as such.
- Pattern screening can be evaded; allowlists, source pins and tool pins need an owner.

## AI tools and existing components

Built with Claude (Cowork, Opus 5.5) as lead engineer and OpenAI Codex for the control API, deployment, Kaggle operations and independent review. The v4 gateway baseline predates the event. IBM Bob was not used.
