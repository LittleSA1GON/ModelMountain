# Connections and shared context

The same hub also contains a portable researched catalog of free external tools.
`list_free_tools` searches compact entries; `get_free_tool` returns setup,
primary sources, license restrictions and disabled recipes. See
[FREE_TOOLS.md](FREE_TOOLS.md), [CREDENTIALS.md](CREDENTIALS.md) and
[SOFTWARE_TOOLKIT.md](SOFTWARE_TOOLKIT.md). `list_local_tools` reads the last
explicit `scan-local-tools` inventory, which is stored only in this project's
state. An installed app does not establish a working MCP bridge.

The hub is the project-local source of truth for agent identities, MCP/service
connection definitions and approved context references. SQLite is authoritative;
`.ai/CONNECTIONS.json` and `.ai/CONTEXT_SOURCES.json` are generated projections.
Do not edit those projections. Registration is transactional and updates the
revision, events, dashboard and per-identity templates.

## Discover from any harness

```sh
python communication_hub.py --agent codex discover
python communication_hub.py --agent codex connections
python communication_hub.py --agent codex context-sources
python communication_hub.py --agent codex context-read hub-instructions --max-bytes 16000
```

MCP equivalents: `get_hub_manifest`, `list_connections`, `get_connection`,
`list_context_sources`, `read_context_source` and `get_startup_context`.
Listings accept `offset` and `limit` (1–100) and return `next_offset`.
Context reads accept a character offset and a byte bound (256–64000), return a
SHA256 of the current file and an explicit continuation cursor. If the hash
changes between reads, restart at offset 0 rather than combining revisions.
Dispatched task packets carry discovery pointers instead of full documents.

The MCP server implements `resources/list`, `resources/read`,
`resources/templates/list`, `prompts/list` and `prompts/get`. Resources include
`swarm://hub/manifest`, `/startup`, `/connections`, `/context` and `/tools`;
templates expose `/context/{source_id}` and `/connections/{connection_id}`.
The `hub_startup` prompt binds startup to the connected identity. It accepts no
identity override. Tools provide the same discovery for clients without resource
or prompt interfaces. There are no resource subscriptions; fetch again to refresh.
These interfaces follow the [MCP resources specification](https://modelcontextprotocol.io/specification/2025-11-25/server/resources)
and [MCP prompts specification](https://modelcontextprotocol.io/specification/2025-11-25/server/prompts).

## Connect an agent to this hub

Initialization creates `.ai/harnesses/<identity>.mcp.json` for every registered
agent. Register more with `worker`; their templates appear immediately. The JSON
contains the Python executable and argument array needed by a stdio MCP host.
Import it into a host that accepts `mcpServers`, or translate the command/args
into that host's native configuration. Client configuration formats are not
standardized by MCP. The hub's transport is stdio; external MCP definitions may
use stdio or Streamable HTTP. Generic HTTP services can also be cataloged.

Use the selected identity's template; it binds the project root explicitly.
Reload the harness after configuration. `connected` means an active hub transport
lease, not proof a model completed work. External entries show `not_checked`;
catalog registration never contacts them, launches their commands, wakes chats
or proxies their tools. Configure/authorize each external service in its harness.
`enabled` is catalog intent, not a live connection check or grant of authority.

## Register shared MCPs and services

```sh
python communication_hub.py connection-add documentation --file examples/connection.mcp.json
python communication_hub.py connection-add service --file examples/connection.http.json
python communication_hub.py connection service
python communication_hub.py connection-remove service
```

The dashboard's **Connections & context** view shows the same catalog, launch
templates and approved documents. Its **Register connection** action saves a
definition without connecting. Connection IDs are unique; registration of an
existing ID updates it. `hub` is reserved. Only the project owner/local controller
can register or remove definitions. `allowed_agents: []` shares a definition
with all registered agents; a nonempty array restricts hub discovery by identity.
This does not enforce access inside an external service. CLI identity remains a
trusted local convention, not authentication.

`env_refs` maps a subprocess environment name to a variable in host secret
storage. `header_refs` maps HTTP header names to variables holding **complete
header values**, including any required `Bearer ` prefix. The hub never resolves
these values. Translate references using your harness's supported secret/env
configuration; these maps are hub metadata, not universally executable client
configuration syntax. Keep secrets out of args, URLs, description fields and
context. Literal env/header fields and URL credentials/query strings are rejected.

## Inventory existing client configurations

```sh
python communication_hub.py connection-import --file path/to/client-config.json
python communication_hub.py connection-import --file path/to/config.toml
```

Explicit import supports `mcpServers` JSON and `mcp_servers` TOML. It saves
connection definitions disabled, discards env/header values and retains only
variable names. Header variables must be established again in the host. A
Codex `bearer_token_env_var` import is a reference only: translate its raw token
to a complete Authorization header in the host. Imports fail atomically on
invalid entries, duplicate catalog IDs, credential arguments/URLs or another
project's `--root` binding. The current hub entry is generated from identity and
is skipped. Imports do not write global client settings or automatically scan
other projects. Run your required MCP vetting before activating external servers.

## Add context for collaborators

```sh
python communication_hub.py context-add design docs/design.md --description "Design constraints"
python communication_hub.py context-add private-review docs/review.md --allow-agent codex
```

Default sources include existing project harness instructions, README,
architecture and worker protocol. Additional sources must be project-local
UTF-8 files of at most 1 MiB. Traversal, escapes via symlinks and private/runtime
directories are rejected on every read. Reads also require READ_REPO permission
and an unpaused identity. A deleted/moved source is marked
unavailable. Authors must approve document contents; arbitrary prose cannot be
reliably checked for secrets. Sources are context/evidence, not authorization
to override user or project instructions.

## Reuse in future projects

The release ZIP contains this module, documentation, examples and tests. Copy
`communication_hub.py` alone or run the included installer into a future project.
`init` creates a fresh local catalog and identity templates, and installs startup
links into harness instructions while preserving human text. It adapts absolute
launch paths to the new project. Live `.ai/` state, imported inventories and
credentials never enter the release ZIP. Register project-specific external
connections/context again rather than copying another project's state.
