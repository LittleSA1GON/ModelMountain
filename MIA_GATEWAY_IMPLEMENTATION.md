# Model Mountain: enforced five-area security pathway using IBM MIA

**Implementation status (October 23, 2026):** All five protection-area decisions are wired into one Python gateway. Unit/integration tests run on CPU, but IBM MIA Q/K capture, attention scores and any reduction in attack success **have not been verified on a Kaggle T4 GPU in this environment**. Do not describe CPU simulations as real model evidence.

## Integrated request flow

`VerifiedIdentity -> ExtractionMonitor -> Direct injection check -> Trusted document/ACL/integrity checks -> MCP signature/TLS/OAuth/definition gate -> IBM MiaLLM(Qwen2-1.5B, capture_qk+attn_tracker) -> calibrated MIA response gate -> secret-output check -> deterministic agent tool authorization -> response or reject`

This gateway does not execute actual MCP tools or company actions. It creates *pre-dispatch* security decisions. Any production application must use trusted OAuth/TLS middleware, tamper-resistant approvals and an actual tool-dispatch integration that cannot bypass these checks.

| Security area | Prevention enforced by Model Mountain | Actual IBM MIA contribution | Evidence today |
| --- | --- | --- | --- |
| Prompt injection | Low-trust prompt/tool-response checks and response gate | Q/K `attn_tracker` risk score, with separately trained score threshold | CPU gate tested; real scores require GPU |
| RAG document poisoning | Per-tenant role checks, allowed sources, SHA-256 versus trusted reference, quarantine | Analysis of surviving retrieved context for instruction hijacking, using same MIA Attention Tracker | CPU checks tested; real scores require GPU |
| Unauthorized AI-agent actions | Independent deny-by-default tool ACL and identity/approval checks | Attention-based risk can withhold a generated tool proposal; a custom hidden-state tool risk probe is future work | CPU action gate tested; no actual actions |
| MCP certificate/update compromise | Validated TLS + OAuth evidence, pinned signed manifests, tool-definition and package-digest checks, no auto-approval of updates | Can analyze untrusted MCP output if preflight passes; does NOT validate TLS/signatures | Synthetic TLS/OAuth tests, genuine Ed25519 verification |
| Model extraction / distillation abuse | Identity-scoped rate limits, output budgets, repeated dataset-harvesting pattern monitoring | No supported general-purpose distillation detector. MIA is **not** substituted for request admission | CPU admission tests only |

## Why MIA alone cannot prevent all five attacks

IBM MIA monitors/steers model internals during vLLM inference. It is not a trusted certificate authority, OAuth validator, document-integrity database, request billing engine, or permission system. Use those controls *outside the model*. A MIA score can supplement them, but it cannot grant access or justify skipping authentication.

For attention-based **prevention**, `MiaRiskPolicy` must be calibrated per model against labeled real IBM MIA scores, with empirically established score direction and threshold. Uncalibrated scores are **telemetry only**. The runtime rejects missing captures, nonfinite values or model/profile mismatch; an error never triggers an uninstrumented fallback. A trained profile needs held-out testing and benign utility checks before production use.

## Test on CPU (no MIA claims)

```bash
python -m pip install cryptography
python -m unittest discover -s tests -v
python -m model_mountain.integrated_demo --output model_mountain_results/integrated_gateway.json
python -m model_mountain.cli --output model_mountain_results
```

## Real MIA on Kaggle (GPU and full IBM environment needed)

Import `Model_Mountain_IBM_MIA_Kaggle.ipynb` and enable Internet plus T4 GPU. The default flags run **CPU tests only**. For the genuine IBM MIA gateway, set `RUN_REAL_MIA=True` and `MAX_REAL_CASES=5`. This creates `real_gateway.json` and `real_gateway.log`. The notebook checks the NVIDIA driver and installs a pinned IBM MIA/vLLM environment in an isolated venv. The subprocess uses `mia_gateway_worker.py` and IBM's Qwen2-1.5B attention-tracker configuration; no input/output fake scores are substituted.

When that smoke test passes, optionally set `CALIBRATE_REAL_MIA=True` to train a small **demonstration-only** threshold from a different set of 4 benign + 4 adversarial examples (may fail if MIA scores do not separate them). The worker then runs with `--profile`. This calibration is **not** an independent security benchmark and is not proof of deployment readiness. Use held-out examples and a larger, diverse sample for real metrics.

The original multi-model benchmark remains in `original_benchmark/`. This specific integrated real-time protection worker intentionally pins Qwen2-1.5B; do **not** silently apply its attention-head config or calibration threshold to another architecture. Extend to other models only after validating their hook configuration and score distribution.

### Example real worker commands (inside MIA virtual environment)

```bash
python mia_gateway_worker.py --repo /path/to/vLLM-Hook --output /tmp/real_gateway.json --max-cases 5
python mia_gateway_worker.py --repo /path/to/vLLM-Hook --output /tmp/qwen2_mia_profile.json --calibrate
python mia_gateway_worker.py --repo /path/to/vLLM-Hook --output /tmp/real_gateway_defended.json --profile /tmp/qwen2_mia_profile.json --max-cases 5
```

Run these as fresh subprocesses with `VLLM_WORKER_MULTIPROC_METHOD=spawn` and an appropriate `MIA_APERTURE_GPU_BYTES` for GPU memory. With the configured system, selected prompts and results are derived from actual vLLM generations and analyzer output. No real business tool can execute.

## Operational limitations

- **MIA instrumented path:** not tested with a real GPU here; documented APIs could need adjustment for the exact installed commit.
- **Prompt detection:** heuristics can miss obfuscated, multi-turn and unknown attacks. Calibrated MIA risk has false positives and false negatives.
- **Documents:** the SHA-256 reference must be kept in a trusted registry separate from attacker-controlled documents. A caller-supplied expected SHA is not trustworthy.
- **MCP:** simulated certificate/OAuth fixtures are not live certificate validation. Live TLS verification is a preflight helper, not an interception-safe network proxy. Production needs pinned, audited registry; OAuth cryptographically verified by trusted middleware; egress controls and DNS rebinding defenses.
- **Tools:** this prototype denies or allows *proposals* but never executes. Production must enforce the result immediately before every dispatch.
- **Extraction:** in-memory counters are not distributed or persistent; rate limits do not stop low-and-slow, multi-account extraction, or copying an open-weight model.
- **MIA telemetry:** do not expose captured activations or `/v1/mia/delivered`; use server authentication or disable delivery routes, and protect logs.

## Code references

- `model_mountain/gateway.py`: five-protection decision path.
- `model_mountain/mia_risk.py`: model-specific threshold calibration and score validation.
- `mia_gateway_worker.py`: actual vLLM + IBM MIA capture/analyze + gateway demonstration.
- `model_mountain/integrated_demo.py`: synthetic end-to-end gateway test.
- `tests/test_integrated_gateway.py`: blocked/allowed behaviors and fail-closed tests.
- `model_mountain/core.py`, `mcp_security.py`, `extraction.py`: underlying security controls.

Sources: [IBM vLLM-Hook](https://github.com/IBM/vLLM-Hook), [IBM MIA configuration and per-request API](https://github.com/IBM/vLLM-Hook/blob/main/docs/configs.md), [OWASP model-extraction defense](https://github.com/OWASP/AISVS/blob/main/1.0/research/chapters/C11-Adversarial-Robustness/C11-03-Model-Extraction-Defense.md).
