# MM-REMOTE-MODELS: remote multi-model MIA runtime and emotion/activation vectors

Owner: `claude` (Claude Cowork, Opus 5.5). Reviewers: 2 distinct identities (task policy).
Status: **implemented and CPU-tested. Not yet executed on GPU.** No REAL_IBM_MIA results exist until the Kaggle run completes.

## What it does

| Piece | File | Notes |
|---|---|---|
| Allowlist + pinned revisions | `kaggle/model_candidates.json` → `kaggle/resolve_revisions.py` → `kaggle/model_allowlist.json` | 40-char commit SHA required. Declared dims are verified against `config.json` at that SHA. `trust_remote_code` and `auto_map` are refused. |
| Download policy | `remote_models.plan_download` | Downloads safetensors, config and tokenizer files only. Pickle (`.bin/.pt/.pkl`) and `.py` files are rejected and listed. Paths are traversal-checked. Total size is capped at 20 GiB. Gated models need the `HF_TOKEN` Kaggle Secret. |
| Compatibility | `remote_models.compatibility` | Checks GPU compute capability against sm75 (the vLLM 0.29 / CUDA 13 minimum), driver CUDA ≥ 13, bf16→fp16 downgrade (warning), the MIA decoder-layer naming allowlist, context length, tensor parallelism, and a VRAM estimate that includes IBM's 4 GiB capture aperture. Problems are reported as blockers; nothing is silently downgraded. |
| Capability matrix | `remote_models.capability_matrix` | `capture_hs`/`steer` work on any layer-locatable architecture. Attention tracker, CoRe, H-Node, tool-call-risk and AttnLink are marked available **only** where IBM ships the heads or probe artifact (`UPSTREAM_CONFIGS` @ `da42003`). |
| Live engine | `mia_runtime.MIAEngine` | Wraps `mia.MiaLLM` with a pinned revision, `trust_remote_code=False` and seed 0. It fails closed with `MIAUnavailable` / `HookEvidenceError`. |
| Vector discovery | `mia_runtime.discover_concept_vectors` | Captures the last-token hidden state at **all** layers, fits a per-layer mean-diff (or pairwise PCA) direction on train, selects the layer by validation AUROC, then reports test AUROC/accuracy with a Wilson CI. Exports IBM `{"dir","avg_proj"}` with SHA-256. |
| Steering A/B | `kaggle/run_mia_kaggle.py::phase_steer` | Sweeps coefficients on **validation** topics, keeping the strongest one whose outputs stay coherent (degenerate rate ≤ 10%). The **test** topics are then scored by an independent emotion classifier (`j-hartmann/emotion-english-distilroberta-base`), with paired bootstrap CIs. |
| Security effect | same | Unsteered vs `refusal`/`uncertainty`/`injection_resistance` vectors on the frozen `evaluation_v1` **test** split. It records expected/forbidden hits and degenerate rate. Tools are never executed. |
| Other MIA use cases | `phase_attn`, `phase_hnode` | Attention Tracker on Qwen2-1.5B (IBM heads) over all 66 evaluation cases, reported as injection-vs-benign AUROC. H-Node hallucination probe on Qwen2.5-1.5B, as an 8-pair sanity check (not a benchmark). |

## Datasets (`examples/emotion_vectors/`, built by `build_dataset.py`, hashes in `MANIFEST.json`)

- `contrast_implicit.json`: 6 emotions (joy, sadness, anger, fear, disgust, calm) × 60 topics, 360 pairs. The positive prompt evokes the emotion through a situation and never names the emotion word (enforced by a test). The negative is a neutral description of the same topic.
- `contrast_explicit.json`: the same set, but the prompt names the emotion. It is kept separate, so token-identity confounding can be measured.
- `contrast_behavior.json`: refusal, uncertainty and injection_resistance, 180 pairs.
- Splits: task_group = topic, with 36 train, 12 validation and 12 test topics. These are disjoint, and validation refuses any leakage.
- Provenance: template-authored by `claude`, not human-annotated. Steering *outcomes* are scored by an independent classifier, never by the vector's own projection.

## Pinned upstream (verified 2026-10-23)

IBM vLLM-Hook `da420038fa6057c8e36c8b5457b1e02afba3cc7c` (package `mia`), with vllm 0.29.0, torch 2.13.0, transformers 5.17.0 and triton 3.7.1.
Indexing: `hidden_states.layers` is **1-based**, and `steering.optimal_layer` is a **0-based** decoder block (see `hs_layer_to_block`).

## Run (owner's PC; cloud sandbox cannot reach kaggle.com / huggingface.co)

```powershell
.venv\Scripts\python.exe kaggle\resolve_revisions.py          # pins SHAs, verifies dims
.\kaggle\run_kaggle.ps1 -Owner <kaggle-username>                # build -> push -> poll -> download
# multi-model:  -Models "Qwen/Qwen2.5-1.5B-Instruct","ibm-granite/granite-3.1-2b-instruct"
# add a new HF model:  kaggle\resolve_revisions.py --add org/name --params-billion 2.0
```

Results land in `model_mountain_results/kaggle/<bundle>/` as `summary.json`, `preflight.json`, `compat.json`, `vectors__*.json`, `steer__*.json`, `attn_tracker.json` and `hnode.json`.

## Known risks and blockers (stated honestly)

1. **Kaggle driver vs CUDA 13.** torch 2.13 cu13 wheels need driver CUDA ≥ 13. If Kaggle's T4 image is older, preflight records the exact version and stops. That is an *external blocker*, not a pass.
2. **T4 has no bf16.** Models run in fp16, and overflow is possible; check the degenerate rate.
3. **Evidence is CPU-tested only.** Every number here comes from CPU synthetic fixtures. No REAL_IBM_MIA effect is claimed until the kernel output exists.
4. **Classifier as judge.** The emotion classifier is a proxy. "calm" maps to its `neutral` label, which is a weaker signal.
5. **Small test splits.** There are 12 test topics per concept (24 activations), so the intervals stay wide by design.
6. **Gated models** (Llama, Mistral) need an accepted license and the `HF_TOKEN` Kaggle Secret.

## Interface offered to Codex (`/api/v1`) and Antigravity (`web/`)

- `GET /models`: rows from `ModelRegistry.matrix(gpu)`, with fields `model_id, revision, compatible, blockers, warnings, runtime_dtype, estimate, capabilities{use_case:{available,config_source,reason}}, license, gated, evidence_type`.
- `GET /vectors`: `VectorArtifact` fields plus `layer_sweep[] {hs_layer, block, val_auroc, val_accuracy}` and `test {test_auroc, test_accuracy, test_accuracy_ci95, n_test}`.
- `GET /reports`: the Kaggle JSON files above, passed through unchanged. The UI must show `evidence_type`, and a missing file means "not run".

## v2 — emotion-vector study (replicating Anthropic 2026, arXiv 2604.07729)

Status: code ready, **no GPU results yet**. Every number in the UI/report must come from a downloaded kernel output.

**Why v1 failed on Kaggle.** Kaggle preinstalls torchaudio built for CUDA 12.8; the pinned torch 2.13.0 is cu130, so
`import vllm` failed ("PyTorch has CUDA version 13.0 whereas TorchAudio has CUDA version 12.8"). v2 uninstalls torchaudio
before the pins, aborts on any failed install step, and only runs phases after `preflight()` imports `vllm` and `mia`.

**Kernels** (`kaggle/build_kernel.py`, driven by `kaggle/run_kaggle.ps1`, one at a time):

| kernel | does |
|---|---|
| `model-mountain-stories` | generator (default Qwen2.5-7B-Instruct, TP2) writes 10 emotions × 60 topics × 3 stories + 180 neutral texts from `stories_spec.json`; drops stories that use the emotion's own words → `stories.json` (generator id + revision recorded) |
| `mm-<model>` | one per target model; reads `stories.json` via `kernel_sources`; phases below |

**Per-model phases** (each in its own interpreter; failures write `status: blocked`, never synthetic data):

1. `emotions` — MIA `capture_hs` all_tokens at 6 depths (25–80%); mean residual over story tokens from token 50 (paper); direction = emotion mean − grand mean,
   with neutral-text PCs (50% variance) projected out; layer chosen on validation topics; reported on held-out test topics
   (10-way accuracy, chance 0.10), implicit scenarios (`contrast_implicit` test split), valence alignment with PC1,
   and **monitoring**: AUROC of each emotion probe at the assistant token for prompt-injection attack vs benign documents.
   Vectors exported in IBM format (`{"dir","avg_proj"}`) with SHA-256.
2. `steer` — MIA `steer` worker, `add_vector` at the selected block, strengths ±0.1/±0.2 × mean token norm (paper units) for
   desperate, calm, happy, angry, afraid. Measured vs unsteered baseline on `behavior_tests.json`: injection attack success
   (canary), benign answer rate, sycophancy on false claims, contrarian rate on true claims, capability (30 exact-answer items),
   degenerate-output rate, and tone shift scored by an independent classifier (j-hartmann distilroberta). Paired bootstrap CIs.
3. `attn` — IBM attention tracker where IBM ships heads (Qwen2-1.5B, Granite-3.1-8B): AUROC attack vs benign.

**Models** (pin with `kaggle/resolve_revisions.py` first): Qwen2.5-1.5B/3B/7B, Qwen2-1.5B, Granite-3.1-2B/8B, Granite-4.0-micro,
Gemma-4-E2B-it, Gemma-4-E4B-it. Gemma 4 and Granite 4.0 are `EXPERIMENTAL_ARCHITECTURES`: MIA's layer hooks are unverified there,
and T4 has no bf16 (Gemma fp16 overflow risk) — the kernel tries fp16 then fp32 and records each attempt.

**Honest limits.** Small open models, 10 emotions (paper: 171), stories written by an open model (paper: Claude Sonnet 4.5),
greedy decoding, keyword/canary graders. Effects are reported with CIs and n; null results are results.

Kernel output hygiene: only `/kaggle/working/mm_results/` is written to the output directory; the IBM clone, HF weights,
bundle and MIA configs live in `/kaggle/tmp` (fallback `/tmp/mm_scratch`). This is an adaptation of the paper's method to
small open models — not a replication, and no claim about subjective experience.
