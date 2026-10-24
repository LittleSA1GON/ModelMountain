# Swarm orchestration hub

Portable, project-local collaboration for any number of registered agents, with
up to 64 active identities at once. This implementation extends the supplied
communication hub ZIP; it retains its transactional SQLite messages, decisions,
file leases, MCP server and dashboard, and adds a working execution scheduler
and a universal connection/context catalog. Version 0.4.2 includes a researched
free API/MCP/software catalog, manual credential checklist and explicit local
application detection. These travel with the portable launcher.
It also provides explicit integration diagnostics and a paged validation matrix.

## Start in a project

Search free tools with `--agent codex free-tools`; get setup, licenses and
primary sources with `free-tool ID`. Use `--downloadable-only` for the free
technical/creative toolkit, `--kind mcp` for servers, and `--all` to inspect
conditional entries and exclusions. `scan-local-tools` inventories registry,
PATH and known app folders without execution or network access; `local-tools`
shows matching catalog entries. All keys/OAuth steps are documented in
[docs/CREDENTIALS.md](docs/CREDENTIALS.md). See [docs/SOFTWARE_TOOLKIT.md](docs/SOFTWARE_TOOLKIT.md)
and [docs/FREE_TOOLS.md](docs/FREE_TOOLS.md) for downloads and source evidence.

Catalog entries are setup recipes, not active external connections. Required
payment methods, trials, paid and retired services are outside the default
free results; noncommercial/model-specific restrictions are explicit.

Run `--agent codex check-integrations --network --local --report INTEGRATION_STATUS.md`
to test all hub MCP functions through isolated processes, bounded public API
reads and known installed CLI/SQLite/Blender operations. No API credentials or
hosted inference are used. View results with `integration-status` or MCP
`list_integration_checks`. Each pass covers only its stated operation; all
catalog entries have explicit tested/pending/unavailable/excluded statuses.
Third-party MCPs still need harness review, authentication/addons and their own
function tests. See [docs/INTEGRATION_TESTING.md](docs/INTEGRATION_TESTING.md).

To install safely into a repository with existing files, extract the bundle to
its own directory and run:

```sh
python scripts/install_into_project.py /path/to/future-project --agents 4
```

This copies only the portable launcher, initializes project-local state and
appends discovery guidance. It preserves existing source and harness rules;
it refuses to replace a different launcher unless `--upgrade` is explicitly used.
An upgrade preserves `.ai/` history. Provider connections still need to be
configured in that project's actual harness.

Extract the ZIP into your project. Do not replace existing AGENTS.md, CLAUDE.md
or GEMINI.md when extracting into an established repository: preserve those
files and use `init` to append the hub discovery link. You can instead copy just
`communication_hub.py` into any project. Python 3.11+ is the only requirement for
the core runtime.

```sh
python communication_hub.py init
python communication_hub.py pool --agents 4 --tokens 100000
python communication_hub.py gui --port 8765
```

Open http://127.0.0.1:8765/. Another project needs its own `.ai/` directory and GUI
port. `init` writes HUB_INSTRUCTIONS.md and adds an idempotent discovery block
to AGENTS.md, CLAUDE.md and GEMINI.md while preserving existing project guidance.
Use `--no-onboard` to skip that step. Project rules and human instructions take
precedence. The hub defaults to the portable launcher's own directory, not the
caller's current working directory; pass `--root` before the command for another
canonical project root or for worktree clients.

For source development or the optional LangGraph runner:

```sh
python -m venv .venv
# Activate .venv, or use its Python executable directly.
python -m pip install -e '.[graph]'
```

`requirements-graph-lock.txt` pins the complete versions tested for this release.
Use `pip install -r requirements-graph-lock.txt` then `pip install -e .` for that
set. Wheels differ by operating system/Python version; this is a version lock,
not a wheel-hash lock. The standalone launcher can also use dependencies from
the interpreter that launches it. It never silently downloads dependencies.

## Connect existing agent harnesses

Default participant identities are `codex`, `claude` and `gemini`. Register any
number of additional external workers, with their actual capability metadata:

```sh
python communication_hub.py worker specialist-1 --capability implementation
python communication_hub.py worker reviewer-1 --capability review
python communication_hub.py --agent specialist-1 context
```

The identity-bound stdio MCP server is launched as:

```sh
python communication_hub.py --root PROJECT_DIRECTORY --agent specialist-1 mcp
```

Add that command to your chosen harness's MCP configuration using an absolute
project path. `configure` previews project-specific configs; it does not apply
global client changes unless `--apply` is explicitly selected. New worker
identities can use the same server command; they are not restricted to the three
built-in providers. CLI identity is a convention, and local filesystem access is
trusted; MCP binds identity to its process but is not remote authentication.

Initialization automatically generates `.ai/harnesses/<identity>.mcp.json` for
every registered identity. The **Connections & context** dashboard view contains
the connection catalog, launch definitions and approved project documents.
Call `get_hub_manifest` or `python communication_hub.py --agent YOUR_ID discover`
to find everything through one entry point. Standard MCP resources and the
`hub_startup` prompt provide the same discovery. See
[docs/CONNECTIONS.md](docs/CONNECTIONS.md) for shared MCP/HTTP definitions,
inventory import, credential references and bounded context reads.

An external harness starts with `get_hub_manifest` and `get_startup_context`, reads HUB_INSTRUCTIONS.md,
and calls `claim_work`. It keeps the run ID and lease token, renews through
`renew_run`, then calls `finish_run` or `fail_run`. The CLI equivalents are
`claim`, `renew-run`, `finish-run --file result.json` and `fail-run`. A command
runner can dispatch work to currently connected external harnesses, but cannot
wake arbitrary desktop chats. A direct claim also works with a trusted CLI
worker without an open MCP transport.

## Automatic command workers

Register an explicit JSON-stdin/JSON-stdout adapter command. The profile file
avoids shell-specific JSON quoting. `examples/worker.external.json` demonstrates
an external profile; `examples/worker.command.json` runs an **offline contract
fixture**, not an LLM. Replace its command with your actual harness adapter.

```sh
python communication_hub.py worker impl-1 --file examples/worker.command.json
python communication_hub.py worker review-1 --file examples/reviewer.command.json
python communication_hub.py plan examples/plan.json
python communication_hub.py run --engine langgraph
```

The command adapter receives one task-local packet on stdin and must emit one
result JSON object on stdout. Your existing harness can read that packet,
perform the work with its own tools/model and emit the contract described in
[docs/WORKER_PROTOCOL.md](docs/WORKER_PROTOCOL.md). It receives SWARM_AGENT,
SWARM_PROJECT_ROOT and SWARM_RUN_ID in its environment. `{python}` selects the
runner interpreter; `{project_root}` expands a project-relative script argument.
Shell evaluation is never used. Credentials remain in your local harness/env;
none are embedded in exports. Explicit command workers are trusted executable
code, not an OS sandbox.

`run --once` executes one scheduler cycle. `run --watch` remains available for
connected external workers and newly added tasks; stop with Ctrl+C. Without
`--watch`, the runner drains immediately executable work and exits when no
command work executed in a cycle, or after `--max-cycles` (default 100). Blocked
tasks and pending external/review work remain durable and visible in `metrics`.
`dispatch` only assigns work; it never launches processes. `run --engine builtin`
uses the same scheduler without LangGraph. The graph engine uses persistent
SQLite checkpoints and `schedule -> execute -> report` nodes. State/claims are
also fenced in the core hub so replay cannot start a command twice. Lost running
commands require inspection; graph checkpoints do not make filesystem side
effects exactly-once.

## Task plans, quality and scaling

`plan` validates a dependency DAG and inserts all tasks/policies in one
transaction. Forward references within the plan are supported. Dependencies
unlock only after completion, including required independent review. The hub
does not invent an objective decomposition using an extra LLM call; the human or
planning agent supplies a concrete plan with acceptance criteria.

Managed tasks default to passing validation evidence and one independent review.
Finishing an implementation creates separately scheduled review jobs that can
run on command or external workers with the `review` capability. Reviewers may
request changes; the implementer cannot self-review. Distinct identity is
enforced, but distinct identity does not prove a different model or person.
Human `review-run` is supported. Review jobs return a `review` verdict with
evidence. Existing manual tasks remain supported until scheduled/marked managed.
Ordinary `complete` or `update-task` cannot bypass a managed task's gates.

Evidence is recorded and inspected by the reviewer; the hub does not itself
execute a worker's claimed project test command or certify an arbitrary string
as true. Configure project adapters to run the required tests and return logs
or artifact IDs. Set a task policy before assignment with `task-policy --json` or
MCP `set_task_policy`. Explicit policy can change review counts, validation,
output allowance, retries, write paths and context artifact references.

```sh
python communication_hub.py pool --agents 8 --per-agent 1
python communication_hub.py pool --agents 2
python communication_hub.py pool --agents 0
python communication_hub.py metrics
```

Scale changes apply on the next dispatch/claim. Zero drains the pool. Lowering
capacity lets existing runs finish; it does not kill them. Routing requires
matching capabilities and permissions, and balances workload before choosing
the configured `cost_rank` (smaller is preferred). You can enable/disable worker
profiles when they have no active runs. `pause` prevents new work and stops a
managed command when the runner observes the pause. Default one task per agent;
raise `--per-agent` only for workers that support concurrent sessions.
The local command runner caps total live command sessions at 64; external
workers may use the higher per-identity allowance through their own harness.

Use isolated checkouts for concurrent editing. `write_paths` are reserved in the
same transaction as capacity and budget. Parent/child overlaps wait. Leases are
advisory, not OS write enforcement. `worktree` supports Git repositories; the
source ZIP itself does not require Git. A worker `cwd` must be an existing
directory within the canonical project, such as a project-local worktree. Map
your adapter's actual edited paths to the canonical ownership policy.

## Token control and recovery

Dispatched context contains task constraints, dependency summaries and artifact/
decision/message IDs, not copied histories. Required constraints are never
silently truncated: an oversized task blocks with an explicit reason. Large
optional indexes are paged, with omissions disclosed. `context_page` provides
bounded inbox/decision/lock indexes; fetch full records on demand. Original
compact startup remains available and deliberately retains open safety records;
it is not a hard-budgeted full transcript. Artifact publication deduplicates
identical content by author, task and name and includes SHA-256 integrity data.

Before starting, the scheduler reserves input bytes (a conservative token
estimate for this packet) plus the policy's output token allowance. Reservations
and usage share the project budget across concurrent workers. Provider-reported
usage replaces the estimate when supplied; otherwise the full reservation is
charged. Metrics distinguish reported/estimated tokens and compare packet bytes
with the same task's uncompressed records. No measured model token savings or
quality improvement is claimed by the offline fixtures. On-demand context,
repeated prompts and tool model calls must be included in the adapter's usage.
Enforce output/cost limits inside your provider adapter; billing cannot be
guaranteed by a scheduler estimate. Reported overruns remain visible and stop
future dispatch.

Leases are renewed by the command runner and explicitly by external workers.
Expiry blocks unknown work and charges its reservation; late results are
rejected. The hub retains file ownership on lost runs. Stop the old process,
inspect its checkout, release its leases explicitly, and use `retry TASK --reason
TEXT`. Explicitly retry-safe failures can retry with bounded exponential delay;
others block. Attempt exhaustion requires a follow-up task. Cancel managed work
as the human with `update-task TASK cancelled`. Command processes are terminated on
timeout/cancellation; after a runner process crash an old worker may still need
to be stopped manually. Keep `.ai/` on a local disk, never a network share.

The runner owns each command's subprocess tree, including descendants that
retain output handles after the adapter exits. Windows uses a Job Object;
POSIX uses a process group. The legacy CLI adapter uses the same bounded runner.
Upgrading the portable launcher preserves existing pool and budget settings
unless `--agents` or `--tokens` is supplied to the installer.

## Verify and export

An offline demo runs real worker processes, parallel tasks, review jobs and
dependencies in a fresh directory. It makes no model calls:

```sh
python communication_hub.py --root tmp/demo demo --agents 4 --engine langgraph
python -m unittest discover -s tests -v
python scripts/package_swarm.py --output dist/swarm-orchestration-hub-0.4.2.zip
python scripts/verify_bundle.py dist/swarm-orchestration-hub-0.4.2.zip
```

Tests require the editable package or PYTHONPATH=src. The optional browser QA
script takes a Playwright module directory and a Python executable. Export is a
curated allowlist: source, GUI, tests, docs, examples, version lock and standalone
launcher. MANIFEST.json contains every file's SHA-256. ZIP CRCs and manifest hashes
are verified. The bundle verifier extracts into a fresh temporary project,
checks the manifest, runs tests against **that extracted source**, and runs the
standalone CLI from an unrelated working directory. It excludes `.ai/`, `.venv`,
credentials, client config, logs, caches and the original ZIP. The old ZIP is
preserved separately in this workspace. Bundling refuses to overwrite an archive.

Core and LangGraph share the same transactional scheduling/review semantics.
Official design references: [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
and [persistence](https://docs.langchain.com/oss/python/langgraph/persistence).
