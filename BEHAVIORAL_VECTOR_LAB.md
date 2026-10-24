# Model Mountain — Behavioral Vector Discovery & Conditional Steering Research

## What's new

This extends Model Mountain's secure RAG, hallucination-risk checks, security rules, and initial IBM MIA demos. It **does not replace** authentication, document provenance, permission checks, or rigorous factual verification.

### Real components added

- `model_mountain/behaviorlab.py`: schema validation, paired-task leakage prevention, candidate **mean-difference** or **pairwise-PCA** vector fitting on real captured activations, validation-only threshold fitting, untouched test metrics, SHA-256 artifact integrity, MIA `dir/avg_proj` tensor export, offline probe scores, experimental steering profile export, and trusted-metadata routing.
- `mia_behavior_capture_worker.py`: GPU-side IBM MIA `capture_hs` capture of positive and negative examples (model/layer metadata, last-token positions, all-or-nothing export, no synthetic fallback).
- `steerability360_worker.py`: optional AI Steerability 360 `ContrastiveFit`, `ContrastivePairs`, `ActivationAdapter`, `SteeringPipeline` experiment. This toolkit's vector representation is kept separate from the MIA `.pt` artifact; no undocumented conversion is assumed.
- `model_mountain/behavior_eval.py` and `mia_behavior_eval_worker.py`: explicit held-out model-output comparison, conservative literal-match metrics, raw response records, and a requirement for independent ground-truth evaluation.
- `examples/behavior_{grounding,injection_resistance,abstention}.json`: tiny contrastive templates with disjoint train/validation/test task groups. **These are not representative training corpora.**
- `examples/heldout_security_reliability.json`: illustrative separate generated-response checks.
- Streamlit `Behavioral vector lab` tab and self-contained Kaggle notebook.

### Model-specific positive and negative examples

Positive examples represent **desired observed behavior**. For grounding, this means answers citing supplied facts; for injection resistance, following the authorized task rather than lower-trust source instructions; for abstention, avoiding unsupported guesses. Negative examples contrast each behavior while holding the underlying task as similar as possible.

The training method fits a direction from **genuinely captured** hidden states, not from prompt text alone. The classifier threshold is fitted on a separate validation task group and scored on held-out test groups. A direction separating labeled activations is **not** evidence that adding it causes safety improvements. Distinguish correlations, interventions, attack outcomes, and benign-task utility.

## CPU: validate datasets (no actual activation capture)

```bash
python -m unittest discover -s tests -v
python -m model_mountain.behaviorlab validate --dataset examples/behavior_grounding.json
python -m model_mountain.behaviorlab validate --dataset examples/behavior_injection_resistance.json
python -m model_mountain.behaviorlab validate --dataset examples/behavior_abstention.json
streamlit run app.py
```

## GPU: IBM MIA real-vector workflow

Do this inside a dedicated, compatible IBM MIA/vLLM environment. IBM docs: https://github.com/IBM/vLLM-Hook/blob/main/docs/configs.md . The example Qwen2 checkpoint is a starting point, not guaranteed to work on Kaggle free T4. Captured activations may be sensitive and must be stored securely.

```bash
python mia_behavior_capture_worker.py \
  --model Qwen/Qwen2-1.5B-Instruct \
  --dataset examples/behavior_grounding.json \
  --layer 14 \
  --output results/grounding_captures.json

python -m model_mountain.behaviorlab fit \
  --captures results/grounding_captures.json \
  --out results/grounding_vector \
  --method mean_diff

python -m model_mountain.behaviorlab export-profile \
  --artifact results/grounding_vector \
  --output results/grounding_profile.json \
  --coefficient 0.5 --allow-experimental
```

`vector.pt` contains a Torch dictionary with `dir` and `avg_proj` fields. `manifest.json` includes the exact model, decoder layer, vector hash, class-separation metrics, split counts and **EXPERIMENTAL_UNREVIEWED** status. The steering profile's `vector_path` must point to a real file on the **GPU server filesystem**. Profiles do not activate steering by themselves. Verify correct hook configuration, layer indices, and model hash. Thresholds do not automatically carry across models, checkpoints, quantizations or prompts.

A minimum of two train, one validation and one test pairs is an interface sanity threshold, **not** an adequate evaluation. For credible claims gather hundreds of diverse independently annotated task groups, avoid lexical shortcuts, choose an intervention layer and coefficient on validation data, and freeze the held-out test set before tuning.

## GPU: paired behavior trial (separate from capture worker)

Run IBM's MIA steering server with `MIA_WORKER=steer` and authentication. The same server may not simultaneously provide the separate capture worker. Then use:

```bash
export MODEL_MOUNTAIN_MIA_API_KEY='YOUR_LOCAL_MIA_API_KEY'
python mia_behavior_eval_worker.py \
  --cases examples/heldout_security_reliability.json \
  --profile results/grounding_profile.json \
  --endpoint http://127.0.0.1:8770/v1 \
  --output results/behavior_ab.json
```

The comparison executes the same test questions with and without requested steering. The OpenAI-compatible response alone **cannot attest** the hook actually ran; inspect the MIA worker/server logs. Literal expected/forbidden markers are only smoke-test metrics, not an entailment verifier or comprehensive prompt-injection red team. Evaluate attack-success rate, unsupported claims, correct answers, false refusals, latency, throughput, VRAM, and cross-task robustness with independent labels.

## Optional IBM AI Steerability 360 experiment

The newer toolkit supports native contrastive fitting with `ContrastiveFit` and `ActivationAdapter` and separately supports vLLM backends. Use its documented API in its own environment (Python 3.12+, `uv`, installation in repository docs):

```bash
python steerability360_worker.py \
  --dataset examples/behavior_injection_resistance.json \
  --model Qwen/Qwen2-1.5B-Instruct \
  --layer 14 --strength 0.5 \
  --output results/steerability360_ab.json
```

This is an **optional genuine model experiment**. The runner imports the toolkit and will fail if it is not installed; it does not create fake results. Toolkit operations have NOT been exercised here against a GPU. Do not interchange the old IBM `activation-steering` package API, the new `steerability` package API, and MIA worker-vector payloads as though they were identical.

## Context-aware routing (experimental)

`select_experimental_profile(TrustedRoutingContext(...), profiles, explicit_opt_in=True)` selects a compatible profile using **trusted application-generated metadata**. It does not interpret model self-declared privilege. Unauthorized tool actions always return `BLOCK_UNAUTHORIZED_ACTION`, even when steering is enabled. It never silently applies a direction without opt-in.

## Current evidence

- All CPU unit tests pass, including the original security controls and new synthetic TEST vector fixtures.
- No actual activation captures or steering-effect measurements were produced by this packaging run.
- A vector can improve probing accuracy and still **worsen** jailbreak susceptibility, grounding, user utility, or privacy. Do not enable as an enforceable control without independent verification.
