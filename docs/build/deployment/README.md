# Model Mountain — Vercel and local deployment

The repository root is the Vercel project root. Root vercel.json builds web/ with
npm ci and npm run build, serves web/dist, and routes /api/v1 to api/index.py.
Do not deploy web/ alone when demonstrating the backend workflow. GPU packages and
credentials are excluded from the function bundle and upload allowlist.

Local review after the frontend build:

```powershell
.venv/Scripts/python.exe scripts/serve_web.py --port 8502
```

Open http://127.0.0.1:8502. The existing Streamlit CPU workbench remains on port8501;
the project-local orchestration dashboard remains on port8776.

Server configuration (set in the deployment environment, never in client JavaScript):
- MODEL_MOUNTAIN_OPERATOR_TOKEN: authenticates remote inference/model/evaluation actions.
- MODEL_MOUNTAIN_REMOTE_URL: fixed HTTPS worker origin; loopback HTTP only for local development.
- MODEL_MOUNTAIN_REMOTE_TOKEN: server-to-worker authentication.
- MODEL_MOUNTAIN_DATA_DIR: optional trusted local report-store directory.

Unconfigured deployments still provide labeled, bounded inert CPU demonstrations.
Requested remote operations fail explicitly; they never turn into simulated successes.
The API cannot independently certify that a worker's hook fired: review linked runtime
artifacts. The Kaggle credential is used by the remote job controller and is not needed
in the browser. Stable interactive ingress and asynchronous Kaggle jobs are distinct
integration modes; only an actually connected mode may be marked available.

Reports store sanitized summaries without prompt/generated text. Local SQLite persists
across local restarts; Vercel /tmp is ephemeral per instance, so durable GPU artifacts
remain with the remote job system. The public demo admission limit is per instance,
not a distributed production quota. Local .ai state is excluded from Vercel uploads;
cloud orchestration must state unavailable until a sanitized synchronization exists.

Deployment sequence: validate CPU suite and build, inspect sanitized upload file list,
login to Vercel, link/create the intended project, deploy, then verify /api/v1/health,
positive/negative requests and every main UI route at the actual returned URL.
No production-readiness or GPU-effectiveness claim follows from a successful deployment.

Local Kaggle bridge (operator opt-in): set MODEL_MOUNTAIN_KAGGLE_ENABLED=1 and
MODEL_MOUNTAIN_KAGGLE_OWNER to the authorized account, plus a strong
MODEL_MOUNTAIN_OPERATOR_TOKEN. POST /api/v1/jobs accepts only model_ids (one or
two pinned catalog models) and phase (full or preflight). It uses the existing
project .venv Kaggle CLI and owner-local authentication. The bridge is always
disabled in Vercel, even if that enable flag is set. Submission is asynchronous,
job records persist locally, and public records include update timestamps.
A filesystem fence prevents concurrent submissions. An uncertain push or polling
outcome keeps the fence for operator reconciliation; never blindly retry it.
Controller process loss does not cancel Kaggle jobs. Inspect the exact recorded
kernel_ref before reconciling a stale fence. No browser value controls shell text,
credential, owner or output path. Output downloads are restricted to mm_results.
Successful kernel completion alone does not establish successful model execution.

Remote HTTP workers receive a server-generated request_id. Independently reviewed
steering attestation must bind that exact request_id, run_id, model/revision, IBM
revision, profile hash, capture artifact and hook artifact; historical evidence
cannot verify a newly requested inference. Worker response fields are allowlisted,
typed and scanned for protected credentials before returning or storing them.
