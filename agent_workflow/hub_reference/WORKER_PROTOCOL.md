# Worker protocol v1

Command workers run exactly the explicit argument array registered by the human.
They read one UTF-8 JSON object from stdin. Logs go to stderr, not stdout.
The process must return one UTF-8 result JSON object on stdout and exit 0.
Stdin/stdout are bounded; 1 MiB per output stream is the runner's maximum.
Nonzero exit, invalid JSON, a timeout or a contract violation fails the run.
The runner does not store raw stderr. Exit errors point to local adapter logs.

## Input

```json
{
  "protocol": "swarm-worker-v1",
  "agent": "impl-1",
  "run_id": "RUN-...",
  "lease_token": "opaque fenced token",
  "project_root": "/absolute/project",
  "expires_at": "2026-10-10T00:00:00+00:00",
  "objective": "Build the project",
  "task": {"id": "A", "title": "Implement A", "acceptance_criteria": ["Tests pass"], "capabilities": ["implementation"]},
  "dependencies": [],
  "artifact_ids": [],
  "inbox_ids": [],
  "decision_ids": [],
  "lock_paths": [],
  "write_paths": ["src/a.py"],
  "output_tokens": 2048,
  "omitted_indexes": {},
  "instructions": "Protocol instructions"
}
```

The cwd is the registered project-local directory. Read the actual repository's
instructions and relevant source using your harness's tools. Fetch referenced
artifacts/messages through the CLI, Python API or identity-bound MCP. Include
all resulting model usage in the final counts. Never include secrets in results.
Keep the lease token within this worker; it fences a particular attempt.

## Result

```json
{
  "summary": "Implemented A and verified its edge cases",
  "evidence": ["src/a.py", "test log artifact ID or path"],
  "validation": {"passed": true, "evidence": ["12 tests passed; log artifact"]},
  "usage": {"input_tokens": 4200, "output_tokens": 950}
}
```

`summary` and nonempty `evidence` are mandatory. Validation is mandatory by
default task policy. Usage is optional only when unavailable; omission charges
the reservation estimate and is visibly labeled estimated. Both token fields
are nonnegative integers and must cover the adapter's entire run, including
tool model calls and retries performed inside the harness. Do not claim an
estimate is provider-reported measurement. The fixture examples use zero
because no model calls occur.

For a review job, input also contains `review_target` with run ID, task ID,
implementer, acceptance criteria and result evidence. Independently inspect
those references, then include:

Dependency and review results use bounded previews. `result_ref` identifies the
`get_task` or `get_run` call that returns the full persisted result, while
`omitted_result_fields` records truncated characters/items. Fetch the complete
result and validation evidence whenever omissions are reported. Required task
criteria and write constraints remain in the packet; large prior results do
not prevent review or dependent tasks from being dispatched.

```json
{
  "summary": "Independent inspection finished",
  "evidence": ["source inspection and repeated test log"],
  "usage": {"input_tokens": 1900, "output_tokens": 350},
  "review": {"approved": true, "summary": "Criteria and edge cases verified", "evidence": ["inspection log"]}
}
```

Use `approved:false` with actionable evidence to request changes. A worker with
the implementation run's identity cannot review it. Multiple required reviews
need distinct registered identities. The human may supply a manual verdict.

External harnesses use the identical result fields in MCP `finish_run`, plus
run_id and lease_token. They call `renew_run` every lease_seconds/3; command
workers are renewed by the runner. `fail_run` accepts error and optional usage.
After reconnect, `get_run` returns the owner's active context and lease token;
other identities receive public evidence with those fields removed.
Lost-response retry of an identical finished result is idempotent. A changed
payload, wrong identity, expired token or cancelled/replaced task is rejected.

## Python integration

```python
from swarm.hub import Hub
from swarm.orchestration import Orchestrator

hub = Hub("/absolute/project")
controller = Orchestrator(hub)
run = controller.claim("actual-registered-identity")
if run:
    # Your harness implements run["context"] and periodically renews the lease.
    controller.finish(run["agent"], run["id"], run["lease_token"],
                      summary="Verified result", evidence=["actual artifact"],
                      validation={"passed": True, "evidence": ["actual test log"]},
                      usage={"input_tokens": 1000, "output_tokens": 200})
```

Each harness may have a different model, provider, tool implementation or
execution framework. The hub is the communication and scheduling authority;
it does not require all workers to use LangGraph or the same model library.
