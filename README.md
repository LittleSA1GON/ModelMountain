# Model Mountain — Enterprise AI Security & Reliability

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
