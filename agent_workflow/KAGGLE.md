# Kaggle implementation handoff

The supplied access token is stored only in the user's `~/.kaggle/access_token`.
On Windows, a restricted file ACL supplies the equivalent intent of chmod 600.
Do not copy the token into this repo, a notebook, agent context, logs or reports.
Authentication success has not yet been checked against Kaggle.

Use the official Kaggle CLI and its access-token authentication. A remote GPU job
must read any model-service credentials through Kaggle Secrets, not notebook literals.
The local Kaggle access token authenticates local CLI requests and need not be
uploaded into the notebook. No remote upload or job was performed by preparation.

Prepare a private local bundle after notebook/source parity is verified:

```powershell
.venv/Scripts/python.exe agent_workflow/prepare_kaggle.py --owner YOUR_KAGGLE_USERNAME
```

Add `--gpu` only for a reviewed GPU job; it enables GPU/internet metadata but leaves
the notebook's real-MIA flags off. The output path must be new to preserve prior
bundles. Code-cell outputs and execution counts are stripped before staging.
Metadata and notebook are staged under `model_mountain_results/kaggle_bundle/`.

Once the bundle and runtime are reviewed, use the official CLI to upload/run the
private notebook, inspect its status and download outputs. Pin Kaggle's runtime,
Python/CUDA/driver/Torch/vLLM/IBM revisions and model checkpoint. Run CPU checks
first; enable real capture/steering separately after compatibility verification.
Record actual hook execution, raw held-out outputs, metrics and failure logs.
GPU selection or a completed notebook does not prove a real hook was exercised.

Ownership: Claude Opus handles MIA implementation and compatibility fixes; Codex
owns evaluation/metric contracts and notebook parity; Antigravity executes bounded
Kaggle reproduction and independently inspects artifacts under MM-GPU-VALIDATION.
Protocol, metrics and security correctness require Codex/Opus sign-off. An unavailable
or incompatible GPU remains a blocker for the real-validation release milestone.

Official references: [Kaggle API](https://www.kaggle.com/docs/api),
[kernel metadata](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels_metadata.md),
[kernel commands and Secrets](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md).

## Current allocation — user override, 2026-10-23

Claude Opus 5.5 leads the majority of technical implementation, architecture,
model/MIA work, evaluation design and all creative/UI design. Codex performs
integration, security/correctness checks and independent verification.
Antigravity is limited to explicitly assigned mundane, repetitive tasks with
exact steps (file inventories, prescribed test/build commands, formatting).
It must not design, implement production code, create datasets/protocols, choose
models/vectors, or approve technical work. Earlier conflicting allocations are
superseded. All work belongs only to Model Mountain, project 16f864bfa1303fc9.
