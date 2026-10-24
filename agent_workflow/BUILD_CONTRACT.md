# Model Mountain build contract

Build the research workbench described in MULTIAGENT_HANDOFF.md and README.md.
The restored v4 source is the baseline, not evidence of a completed product.
The Python package remains `model_mountain`. No production-readiness claim is authorized.

Deliver a usable local dashboard, application boundary, protected ingestion and retrieval,
model backend integration, artifact inspection, reproducible evaluation and packaging.
CPU mode must run without model downloads. Real inference and steering are explicit modes.

Before parallel implementation, MM-CONTRACTS freezes the request, document, backend,
decision, inference-record and report interfaces with examples and compatibility tests.
Identity comes from authenticated application code. Documents carry tenant, source,
ACL, integrity and provenance metadata anchored in trusted ingestion. Model output cannot
grant authority. Inference records include run/case/condition IDs, evidence type, model
and revision, retrieval IDs, requested/applied steering distinction, profile hash,
seed, timing, verdict, failure reason and runtime provenance. Missing values stay unknown.

MM-PROTOCOL independently specifies held-out groups, annotation rules, leakage checks,
metric denominators, validation-only tuning and failed/abstained-case accounting.
Compare A bare generation, B secure RAG, C secure RAG plus steering, and D external
controls plus RAG plus steering on the same frozen cases. Baseline attack conditions
use inert tool sinks; benchmark ablations never execute unauthorized real actions.
Failures remain visible in aggregate denominators. Report attack success, false
refusals, answer correctness, supported claims, abstention, p50/p95 latency, sample
sizes and uncertainty. VRAM is measured only on supported GPU runtimes, otherwise null.

Real MIA results require a pinned dedicated Linux/CUDA environment, model revision,
IBM revision, dtype, device, layer, tensor shape, seed, genuine hook evidence and
paired outputs. Failed capture cannot fall back to synthetic data. A documented
incompatibility is a blocker for the real milestone, not a successful experiment.
CPU synthetic classifier performance cannot establish causal safety benefit.

Every implementation includes positive, negative and failure tests; changed interfaces;
commands and environment; actual logs; remaining limitations; and independent review.
Run the complete CPU suite and integrated demo before integration/release. Preserve
opt-in flags, conservative failure behavior and evidence labels. Sensitive captures,
private corpora, credentials and raw enterprise outputs stay out of commits and artifacts.

Completion gates: reviewed application implementation; reproducible clean installation;
passing CPU checks and notebook parity; verified dashboard workflows; then separately
real inference and A/B/C/D outcomes. An unavailable GPU cannot be replaced by a CPU pass.
Deployment, external messages and paid infrastructure are outside this preparation.

Current allocation follows the latest explicit user instruction: Claude Opus5.5 leads
majority technical/creative implementation, including UI and evaluation. Codex handles
integration and independent correctness verification. Antigravity performs only
explicitly assigned mechanical chores and has no implementation/design/review authority.
Kaggle reproduction follows agent_workflow/KAGGLE.md and uses no embedded credentials.

## Current allocation â€” user override, 2026-10-23

Claude Opus 5.5 leads the majority of technical implementation, architecture,
model/MIA work, evaluation design and all creative/UI design. Codex performs
integration, security/correctness checks and independent verification.
Antigravity is limited to explicitly assigned mundane, repetitive tasks with
exact steps (file inventories, prescribed test/build commands, formatting).
It must not design, implement production code, create datasets/protocols, choose
models/vectors, or approve technical work. Earlier conflicting allocations are
superseded. All work belongs only to Model Mountain, project 16f864bfa1303fc9.
