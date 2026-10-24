# Application contract v1

The Vercel control plane is CPU-only; Kaggle executes GPU jobs and downloads.
Prefix: `/api/v1`. Lists return `{ "items": [...] }`; errors return
`{ "error": { "code": "...", "message": "..." } }` with a non-2xx status.
GET: `/health`, `/models`, `/vectors`, `/reports`, `/orchestration`, `/jobs`, `/jobs/{id}`.
POST: `/inference`, `/evaluations`, `/models/register`.

Remote inference, downloads and evaluations require the server-configured operator
credential. Judge/public access allows only bounded, explicitly labeled simulations
and sanitized reports. Browser input cannot supply trusted identity, authorization,
server URLs, executable code, model-local paths, or approved document provenance.

Inference input: `model_id`, `question` (1..8000 chars), `mode` (simulation/remote),
optional `profile_id`, `max_output_tokens` (1..512). Server-side authentication supplies
tenant and principal. Model registration requires repository ID plus immutable revision;
upstream model-code execution is disabled by default.

Inference output: run ID, evidence type, model/revision, mode, decision, answer, reasons,
citation IDs, latency, requested/verified steering, profile hash, attestation reference
and error. Unknown measurements are null. Simulations use `CPU_SYNTHETIC`. Model text
never grants tool permissions; all benchmark tool proposals go to inert action sinks.

Capabilities are independent: inference, hidden states, attention tracking, steering,
CoRe, H-Node, science hallucination and AttnLink-U. Per-model states are unverified,
compatible, verified, unsupported or blocked. Library support is not runtime evidence.
Artifacts bind model/revision/layer convention/token positions/dimensions/dtype,
dataset and split hashes, and IBM/runtime versions. Requested hooks are not verified hooks.

Runs: queued/running/succeeded/failed/blocked/cancelled. Case records retain condition,
task-group/split, evidence type, output-artifact reference, outcome/failure, latency and
provenance. Failed cases stay in denominators; report observed ASR plus a pessimistic
bound treating unknown attack outcomes as successes. Correct abstention depends on
evidence sufficiency. Literal citation overlap is a proxy, not factual truth. Vector
classifier scores are separate from held-out causal intervention outcomes.

Migration uses adapters for current VerifiedIdentity, Document, GatewayRequest and
callable backends; Streamlit CPU workflows remain supported. This versioned wrapper
does not weaken authorization or impose the old Qwen-only telemetry binding on all models.
Examples in examples.json are synthetic fixtures, not recorded measurements.
