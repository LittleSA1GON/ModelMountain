# Model Mountain

**A security gateway for company AI assistants.** Five implemented checks target prompt injection, poisoned knowledge, data exfiltration through tools and links, malicious tool updates, and model copying. A Kaggle GPU pipeline uses IBM vLLM-Hook (MIA) to measure and steer three open models' internal state; see [docs/RESULTS.md](docs/RESULTS.md) for what has actually run.

SpartHill Hacks 2026 · IBM AI Challenge · **Live demo: https://model-mountain.vercel.app** · Submission text: [DEVPOST_SUBMISSION.md](DEVPOST_SUBMISSION.md)

## Why

Assistants that read email, documents and tickets and can call tools can be redirected by the text they read. Documented cases include EchoLeak (CVE-2025-32711), Invariant Labs' MCP tool-poisoning and GitHub MCP reports, PromptArmor's Slack AI report, the malicious `postmark-mcp` package, CamoLeak, PoisonedRAG, and distillation campaigns reported by Anthropic in Feb 2026. The full cited list is in `model_mountain/defenses.py` (`INCIDENTS`) and on the app's Defenses page.

## The five defenses

| # | Defense | What it stops | Code |
|---|---|---|---|
| 1 | Prompt-injection firewall + MIA Attention Tracker | Untrusted text acting as instructions | `core.py`, `gateway.py`, `kaggle/run_mia_kaggle.py:phase_heads` |
| 2 | RAG integrity and access control | Tampered or poisoned passages, cross-tenant retrieval | `rag.py`, `core.py` |
| 3 | Exfiltration guard (rendered output + tool calls) | Auto-loaded images, data-carrying links, unapproved recipients, private-to-public flows, the "lethal trifecta" | `egress.py`, `core.py:tool_decision` |
| 4 | MCP supply-chain guard | Poisoned tool descriptions, rug-pull updates, impersonated servers | `mcp_security.py` |
| 5 | Model-extraction guard | Output harvesting, including coordinated multi-account campaigns | `extraction.py` |

Every request runs through `ModelMountainGateway.evaluate`, which returns a per-stage `trace` of what each check decided.

## Model internals (IBM MIA, Kaggle 2× T4)

Pipeline for Qwen2.5-1.5B-Instruct, IBM Granite-3.1-2B-Instruct and Gemma-4-E4B-it (E2B fallback), pinned revisions. Only outputs that actually completed on Kaggle are reported:

- **Emotion vectors** (method of Anthropic 2026, arXiv 2604.07729, adapted to small open models): story activations, neutral-PC denoising, layer chosen on validation topics, held-out test accuracy.
- **Attention heads for injection detection**: every head captured with MIA `capture_qk`, important heads selected with the Attention Tracker criterion (Hung et al., NAACL 2025 Findings), held-out AUROC; exported as IBM `attention_tracker` configs.
- **Protective steering**: calm / desperate vectors on held-out Tensor Trust hijacking attacks, TruthfulQA and side-effect checks, strength chosen on validation only.
- **User-adjustable steering**: the Steering page builds an opt-in profile (model, vector, strength, layer, phase, positions) bound to the vector's SHA-256 and shows the measured effect at the nearest strength that ran. Changed outputs versus the unsteered run are reported as corroboration that the steering request took effect, not as an independent hook attestation.

Results: [docs/RESULTS.md](docs/RESULTS.md). Each number there traces to a downloaded Kaggle output. If a run did not complete, the exact blocker is recorded instead.

## Quick start (CPU, no model downloads)

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
cd web && npm ci && npm run build && cd ..
python scripts/serve_web.py          # http://127.0.0.1:8502 (UI + /api/v1)
python -c "from model_mountain.defenses import run_lab; import json; print(json.dumps(run_lab()['scenario_suite'], indent=1)[:2000])"
```

GPU runs (Kaggle): `python kaggle/build_kernel.py --owner <user> --stories`, then `--model <id>` for each model; ingest with `python scripts/ingest_kaggle_results.py <mm_results dirs...>`.

## Honest limits

- The live site runs the rule engine on CPU with inert fixtures. It never runs a language model, never executes a tool and never sends data anywhere. Results are labeled `CPU_SYNTHETIC`, `REAL_IBM_MIA` or `CONFIGURATION_ONLY`.
- GPU results use small models and small held-out sets; intervals are wide, and null results are reported as such. Emotion vectors are statistical directions, not claims about model feelings.
- Pattern screening can be evaded; allowlists, source pins and tool pins need an owner.

## AI tools and existing components

Built with Claude (Cowork, Opus 5.5) as lead engineer, OpenAI Codex for API/deployment/Kaggle operations and independent review, and Claude Code CLI for Windows test runs. Google Antigravity did early mechanical checks; its UI and evaluation set were withdrawn. The v4 baseline (gateway, RAG, MCP, extraction checks, Streamlit dashboard) predates the event. See `docs/build/hackathon/DISCLOSURE.md`.

---

# Reference: v4 baseline notes

**SpartHill IBM Hackathon — working CPU research prototype + experimental IBM MIA GPU integration.**

Model Mountain continues the earlier security prototype with **secure RAG, reproducible grounding checks, conservative abstention, hallucination-risk evaluation, paired activation steering, real hidden-state capture/vector-learning scripts, and optional IBM CoRe reranking** while retaining its existing vulnerability, agent, MCP, and extraction checks.

It is **not a production AI firewall**, **not a proven hallucination reducer**, and **not a verified GPU deployment**. All CPU examples are explicitly labeled simulations. Running the MIA scripts successfully on a compatible GPU is required before reporting real internal-model results. Even a successful hook run does not establish mitigation effectiveness without independent held-out tests.

## Implemented capabilities and evidence boundaries

| Component | Implemented | Verified here | Important limitation |
|---|---|---|---|
| Prompt-injection preflight | Regex heuristics | Unit tests | Easy to evade; false positives possible |
| Secure RAG | Trusted hash registry, tenant/role/source checks, poisoned-source quarantine, lexical retrieval | CPU tests | Registry must be provisioned by trusted ingestion; lexical fallback is not semantic search |
| Answer grounding | Citations, source text matching, numeric mismatch checks, conservative review/abstention | CPU tests | Exact-source checks are **not** semantic truth/entailment detection |
| Agent/MCP/model-extraction defenses | Existing deterministic gateway, simulated authorization, signature/pin checks, quota monitor | CPU tests | No actual enterprise actions or distributed counters |
| IBM MIA Attention Tracker | Existing optional GPU worker | Interface/code only | Actual GPU capture not validated here |
| IBM MIA hidden-state capture | New `mia_reliability_worker.py` | Static review only | Requires compatible GPU + IBM MIA |
| Learn contrastive steering vector | New `model_mountain.steering` | API + synthetic/mocked tests | Training labels may be confounded; no validated causal security direction |
| IBM MIA real activation steering | New served `MIASteeringClient` and offline paired worker | Request format mocked | Must verify genuine MIA worker and hold-out outcome |
| IBM MIA CoRe reranker | New optional `mia_rerank_worker.py` | Static review only | Capture config and GPU needed; ranking is relevance, not truth |
| Evaluation & dashboard | CPU evaluation CLI, streaming security simulation, Streamlit reliability tab | CPU run/tests | Fixture success is not real LLM performance |

## Fastest local start (CPU; no model downloads)

```bash
cd Model_Mountain
python -m pip install cryptography
python -m unittest discover -s tests -v
python -m model_mountain.evaluation --output model_mountain_results/reliability.json
python -m model_mountain.cli --output model_mountain_results/security
python -m model_mountain.integrated_demo --output model_mountain_results/integrated_gateway.json
```

Optional GUI:

```bash
python -m pip install streamlit
streamlit run app.py
```

The RAG demo is a deterministic **extractive fixture**, not an LLM. SourceRegistry.trusted_fixture automatically pins local test content **for demonstration only**. In real deployment, pins and ACL metadata must originate from a protected administrator-controlled ingestion pipeline.

## RAG Python API

```python
from model_mountain.core import Document
from model_mountain.rag import ModelMountainRAG, SourceRegistry, RAGRequest

source = Document.approved('policy', 'The reimbursement limit is $500 per request.')
rag = ModelMountainRAG((source,), SourceRegistry.trusted_fixture((source,)))
print(rag.answer(RAGRequest('What is the reimbursement limit?')))
```

For a real generator, supply `backend(system_instruction: str, context: str) -> str`. It must produce a directly supported quoted sentence followed by `[doc_id]` for automatic release. Paraphrases are withheld unless independently verified. The existing `ModelMountainGateway` supports an optional `require_extractive_grounding=True` output gate, while preserving its original opt-in/offline MIA mode and independent authorization checks.

## Genuine IBM MIA steering workflow (GPU required)

**IBM MIA documents:** https://github.com/IBM/vLLM-Hook ; https://github.com/IBM/vLLM-Hook/blob/main/docs/configs.md

IBM's validated vLLM-Hook stack is version-specific (vLLM 0.29, its MIA plugin, an NVIDIA CUDA-compatible Linux environment). Follow IBM's `requirement.txt` and its own installation instructions in a **dedicated environment**, rather than mixing dependencies with your system Python. The Kaggle notebook includes an optional installer; Kaggle T4 compatibility and its CUDA driver are not confirmed.

1. In the IBM/MIA environment, run **real labeled activation capture** with a compatible `capture_hs` configuration. Example uses a Qwen2-1.5B hidden-state config that must exist in your installed IBM checkout:

```bash
python mia_reliability_worker.py \
  --model Qwen/Qwen2-1.5B-Instruct \
  --config /path/to/vLLM-Hook/model_configs/hidden_states/Qwen2-1.5B-Instruct.json \
  --examples examples/contrastive_prompts.json \
  --layer 14 --output model_mountain_results/capture
```

2. Fit a **candidate** direction using separately labeled activation tensors:

```bash
python -m model_mountain.steering \
  --positive model_mountain_results/capture/positive.pt \
  --negative model_mountain_results/capture/negative.pt \
  --output model_mountain_results/capture/vector.pt
```

3. Create a JSON profile based on [`examples/steering_profile.template.json`](examples/steering_profile.template.json). `vector_path` must be the absolute location of the `.pt` vector accessible to the IBM worker. `optimal_layer` uses a 0-based decoder-block index. Start with a low coefficient; examine sign/strength and benign utility on held-out data rather than assuming any direction is beneficial. Confirm the hidden dimension matches the model and the captured layer corresponds to the steered block.

4. Run the **offline real MIA paired experiment** under the dedicated GPU environment:

```bash
python mia_steering_experiment_worker.py \
  --profile model_mountain_results/capture/steering_profile.json \
  --output model_mountain_results/mia_steering_ab.json
```

It uses `MiaLLM(..., worker_name='steer')` and generates with hooks **off/on** for the same model and task. **It is only a technical intervention comparison**: train and evaluate on different prompts and quantify false refusals, legitimate task completion, supported-claim rate, injection success, and runtime overhead before claiming any benefit.

5. Optional served mode: launch from IBM repository root with `MIA_WORKER=steer` and a dedicated server, **on trusted loopback or HTTPS**. Pass a valid, operator-approved profile to:

```bash
export MODEL_MOUNTAIN_MIA_API_KEY='YOUR_LOCAL_AUTH_TOKEN'
python -m model_mountain.evaluation --endpoint http://127.0.0.1:8770/v1 \
  --profile model_mountain_results/capture/steering_profile.json \
  --output model_mountain_results/real_model_comparison.json
```

The API call uses IBM's supported `extra_body={"vllm_xargs":{"steer": json.dumps(...)}}`. The endpoint's response alone **cannot attest** that the hook ran. Verify the MIA server configuration/logs. If inference fails, the code does not silently switch to unsteered inference.

6. Optional genuine CoRe reranking:

```bash
python mia_rerank_worker.py \
  --model Qwen/Qwen2-1.5B-Instruct \
  --config /path/to/vLLM-Hook/model_configs/core_reranker/Qwen2-1.5B-Instruct.json \
  --output model_mountain_results/core_reranking.json
```

This is a separate GPU experiment after tenant/source verification, not the default CPU lexical retriever. Running CoRe and steering in different processes avoids pretending IBM's capture and steering workers operate simultaneously in a single engine.

## Measuring real effectiveness

Compare (A) bare model, (B) authorized RAG, (C) authorized RAG with MIA steering, (D) complete external security controls + RAG + steering. Use **independent held-out prompts and poisoned documents** and report attack success, supported-claim rate, appropriate abstention, correct answer rate, false refusals, p95 latency and VRAM. The bundled JSON scenarios are tiny sanity checks, **not a scientifically meaningful statistical benchmark**. A verbatim quote from a poisoned but approved source could still be factually wrong.

## Files

- `model_mountain/rag.py`: trusted source registry, authorization, retrieval, conservative claim/citation checks, CPU extractive fixture.
- `model_mountain/steering.py`: strict IBM MIA served client, vector-learning utility and profile format.
- `model_mountain/evaluation.py`: local fixture and real-model paired evaluation.
- `model_mountain/gateway.py`: existing integrated security gateway plus opt-in grounding gate.
- `mia_reliability_worker.py`: genuine IBM MIA capture_hs training data acquisition.
- `mia_steering_experiment_worker.py`: genuine IBM MIA paired steering/unsteered generation.
- `mia_rerank_worker.py`: genuine IBM MIA CoRe relevance experiment.
- `mia_gateway_worker.py`: retained attention-based model security gateway.
- `app.py`: interactive research dashboard.
- `Model_Mountain_Kaggle.ipynb`: self-contained restore, offline tests, optional GPU execution.
- `tests/`: original security tests and new reliability/steering tests.

## Deployment warnings

Never treat untrusted documents as instructions. Enforce tool permissions outside the model. Keep tenant-specific content and activations protected; raw activations can contain sensitive information. Require independent source validation before granting document trust. Keep steering profiles signed/pinned and model-specific; they may reduce benign performance or worsen security. Use a separate model verification step for factual paraphrases and high-stakes decisions. Do not expose unprotected `/v1/mia/delivered` or a public model management API.

## Model Mountain v4: behavioral vector discovery

See **[BEHAVIORAL_VECTOR_LAB.md](BEHAVIORAL_VECTOR_LAB.md)** for reproducible training, export, paired real inference, optional IBM AI Steerability 360 experiments, and limits. The new dashboard tab provides dataset validation and inspectable manifest metrics. New files: `model_mountain/behaviorlab.py`, `model_mountain/behavior_eval.py`, `mia_behavior_capture_worker.py`, `mia_behavior_eval_worker.py`, `steerability360_worker.py`, `examples/behavior_*.json`, `tests/test_behaviorlab.py`. These additions preserve existing security, RAG and MIA functionality. All new trained directions are **experimental**; none is preinstalled as a production defense.


## Multi-agent workflow handoff

Start with [`AGENTS.md`](AGENTS.md), [`MULTIAGENT_HANDOFF.md`](MULTIAGENT_HANDOFF.md), and [`agent_workflow/TASK_BOARD.md`](agent_workflow/TASK_BOARD.md). Each coding agent has a scoped brief under `agent_workflow/roles/`. `pyproject.toml` supports editable installation. The renamed Python import is `model_mountain` throughout the project; the Kaggle notebook is regenerated using the renamed source.
