<!-- SWARM-HUB:GENERATED sha256=4878245179672c3df16cf5676f0b95ecca944cf2b920be8f568437975356039f -->
# Swarm orchestration hub

Read the project's human instructions before using this hub. User instructions
take precedence. This project owns its `.ai/` state. Never copy `.ai/` to another
project, or enable another project's MCP server in this session.

Start with `python communication_hub.py --agent YOUR_ID context` or MCP
`get_startup_context`. Use your registered identity, not the provider/model name
of a different participant. If unregistered, ask the project owner to register
you with `worker`. Do not impersonate `human`. CLI --agent is an identity
convention, not authentication; only trusted local users should access the hub.

All connection discovery and approved shared context live inside this hub.
Call `get_hub_manifest` (CLI: `--agent YOUR_ID discover`) or read the MCP resource
`swarm://hub/manifest`. `list_connections` / `get_connection` discover the hub
and registered external MCP/services; `list_context_sources` /
`read_context_source` page through project instructions and approved documents.
MCP resources/list and prompts/list also expose discovery and a hub_startup
prompt. Clients with tools only can use the equivalent discovery tools.
Each registered identity has `.ai/harnesses/YOUR_ID.mcp.json`, generated on
initialization and refreshed after worker changes. Use that exact identity.
The central catalogs are `.ai/CONNECTIONS.json` and `.ai/CONTEXT_SOURCES.json`.
Connection metadata never grants permission or proves a service is connected.
External services require explicit harness configuration and authorization;
credentials stay in environment/host secret storage. Never paste credentials
into definitions, command arguments, context files, messages or artifacts.

The embedded free API/MCP/software catalog travels with the portable hub.
Initialization also creates neutral research and testing guides under docs/ when
those paths are available and the files are missing; existing files are preserved.
Search `list_free_tools` and fetch selected `get_free_tool` details only when
needed. `list_credential_requirements` lists manual key/OAuth/account steps;
`list_local_tools` reads the last explicit software inventory. CLI equivalents:
`free-tools`, `free-tool`, `credential-requirements`, `local-tools`.
The controller can run `scan-local-tools` to inventory registry/PATH and known
application folders without launching apps, inspecting secrets or contacting
services. Inventory stays in this project's state and never ships in exports.
Use `free-tools --downloadable-only` for free technical/creative software.
Default catalog excludes paid/trial/card-required/retired services; --all shows
restrictions. Noncommercial and model/asset-specific licenses remain explicit.
`free-tool-template ID` emits a disabled definition, never installs or connects.
Verify current quotas, software versions and permissions before activation.

Use `list_integration_checks` / `swarm://hub/integration-checks` for the last
explicit validation, fetched only when needed. CLI `check-integrations` tests
every hub MCP function in disposable state; --network opts into bounded public
GETs and --local into known CLI/SQLite/Blender fixture checks. No credentials or
hosted inference are used. External MCPs are not automatically installed or
connected. Each pass covers its stated operation; pending setup is explicit.
Reports stay project-local and never ship in exports. See docs/INTEGRATION_TESTING.md.

For managed work, call `claim_work`. Retain the returned run ID and lease token;
renew via `renew_run` before expiry (every lease_seconds / 3). After reconnect,
retrieve your existing run via `get_run` using the active_run ID in your task
record; only the owner receives its context/lease token for recovery.
Read the task's acceptance criteria, dependencies, local AGENTS.md/CLAUDE.md/GEMINI.md and the
relevant inbox before editing. `context_page` lists bounded inbox/decision/lock
indexes; fetch exact records or artifacts only when needed. Refer to artifacts
by ID, exchange concise findings and evidence, and avoid repeated transcripts.
The context bound applies to dispatched packets, not all on-demand reads.

Use isolated checkouts for concurrent code edits. Soft leases coordinate file
ownership; they are not an OS sandbox. Respect `write_paths` and existing leases.
Do not alter hub runtime/state by hand. Managed task state is changed only by
run APIs, independent review, explicit human retry or cancellation.

Finish through `finish_run` with summary, nonempty evidence, validation
{passed:true,evidence:[...]}, and usage {input_tokens:N,output_tokens:N} when
measured. Include every model/tool-model call in usage. Missing usage is charged
at the reservation estimate. A result is not complete until independent review
requirements are met. `review_run` requires a different identity with `review`
capability (or the human), a verdict and evidence. A review job returned by
claim_work must also include review={approved,summary,evidence} in finish_run.
Fail with `fail_run`; retry uncertain side effects only after inspection.
Never claim tests ran, agents responded, or token savings were measured without
evidence. Never publish secrets or hidden model reasoning. Completion does not
authorize merge, push, deployment, or messages outside this local hub.

See README.md, docs/CONNECTIONS.md, docs/FREE_TOOLS.md, docs/CREDENTIALS.md,
docs/SOFTWARE_TOOLKIT.md, docs/WORKER_PROTOCOL.md, examples/plan.json and `--help`.
Core needs Python 3.11+. Optional LangGraph runner: install `.[graph]` and use
`run --engine langgraph`. MCP registration is a client-specific setup step; the
hub cannot automatically wake arbitrary desktop chats. No API credentials ship.
