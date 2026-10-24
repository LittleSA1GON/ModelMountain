# Multi-Agent Handoff — Model Mountain v4

## Mission

Develop a credible, testable **enterprise AI security and reliability research workbench** that integrates conventional authorization and provenance controls with secure RAG, hallucination-risk checking, and IBM MIA activation-vector experimentation. It is NOT production-ready.

## Current baseline (do not overclaim)

- Five-area security framework: prompt-injection heuristic screening, document access/integrity policy, agent tool authorization, MCP identity/integrity checks, and request-extraction admission rules.
- Conservative secure RAG with source pins, ACLs, evidence/citation checks and abstention; local CPU demo is extractive simulation, not live semantic entailment.
- IBM MIA workers for attention/risk, hidden-state capture, steering comparisons and CoRe reranking: implemented **code paths**, not GPU-validated by this release.
- Behavioral Vector Lab: paired examples, split isolation, mean-difference/pairwise PCA candidate vector fitting, classifier metrics, tamper detection and conditional experimental profile routing. CPU synthetic vector results are not a real-model safety claim.
- Streamlit dashboard and portable, self-contained Kaggle notebook.

## Repo map

- `model_mountain/core.py`: security fixtures, document and prompt checks.
- `model_mountain/gateway.py`: centralized security decision path and authorization.
- `model_mountain/mcp_security.py`: MCP verification and change integrity.
- `model_mountain/extraction.py`: request admission and extraction-abuse heuristics.
- `model_mountain/rag.py`: authenticated document retrieval and grounding gate.
- `model_mountain/evaluation.py`, `behavior_eval.py`: reliability/held-out evaluation.
- `model_mountain/behaviorlab.py`, `steering.py`: capture-artifact learning and experimental steering profiles.
- `mia_*_worker.py`, `steerability360_worker.py`: optional real-model experiments.
- `app.py`: Streamlit UI; `tests/`: unit tests; `examples/`: tiny synthetic fixtures.
- `Model_Mountain_Kaggle.ipynb`: standalone Kaggle restoration + optional MIA setup.

## Definition of done for agent contributions

1. Specify the measurable hypothesis, threat model, data provenance, failure behavior and acceptance tests.
2. Implement behind an explicit flag if it depends on unvalidated model-internal behavior.
3. Add independent tests (including negative cases and unauthorized requests).
4. Preserve report evidence_type markers (CPU_SYNTHETIC vs LIVE/REAL), no invented measurements.
5. Run full unit suite and one CPU integrated demo before handoff. Record environment, versions and test output.
6. For GPU changes: record exact IBM vLLM-Hook revision, model checkpoint, dtype, layer, device, tensor shape, latency, seed, control vs steering outputs and held-out outcomes. A successful API call alone is insufficient to attest a hook fired.

## Immediate high-value workstreams

Refer to `agent_workflow/TASK_BOARD.md` for owner scopes, acceptance criteria and coordination. First milestone is an end-to-end **real inference** evaluation with at least one supported model and both vulnerable/benign tasks; compare A) no RAG/protection, B) secure RAG, C) RAG+MIA steering, D) full external security controls+RAG+steering, with documented limitations.

## Quick start

```bash
python -m pip install -e '.[vector-lab]'
python -m unittest discover -s tests -v
python -m model_mountain.cli --output model_mountain_results/security
python -m model_mountain.evaluation --output model_mountain_results/reliability.json
python -m model_mountain.integrated_demo --output model_mountain_results/integrated_gateway.json
```

Optional dashboard: `python -m pip install -e '.[dashboard]' && streamlit run app.py`.

## Compatibility caution

The Python import is `model_mountain`, not `model-mountain` or `Model Mountain`. External scripts importing `icewall` must be updated. Environment variable: `MODEL_MOUNTAIN_MIA_API_KEY` (set only in your local environment). Output paths default to `model_mountain_results`. The Git repository and project root can be `Model_Mountain`.
