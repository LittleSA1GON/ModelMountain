# Integration validation

Run checks explicitly in the project that will use the connections:

```sh
python communication_hub.py --agent codex scan-local-tools
python communication_hub.py --agent codex check-integrations --network --local --report INTEGRATION_STATUS.md
python communication_hub.py --agent codex integration-status --status pending
```

Replace codex with your registered identity. Without `--network` and `--local`,
only the hub's own functions are executed. MET Norway requires a public contact
email/URL; pass `--contact YOUR_PUBLIC_CONTACT` to identify your requests.
Do not put API keys or private identifiers in contact information.

Every current hub MCP function is exercised using real independent stdio
processes in disposable state. Tests cover collaboration, context/resources,
task creation, ownership, leases, results, independent review, failure reporting,
identity rejection and discovery. Fixture participant names do not prove actual
model agents participated or that model token savings were measured.

Network checks use fixed public URLs, a maximum of four concurrent GETs, a
12-second request timeout and a 1 MiB response limit. They validate expected
JSON/Atom/text content. They do not read credentials, make inference calls,
send messages, create account data, or execute arbitrary connection commands.
One successful read is evidence for that operation only. API write operations,
OAuth scopes, model quality and provider-wide availability need separate tests.

Local execution checks use known CLI version commands, an in-memory SQLite
create/insert/select and, when Blender is detected, a factory-startup mesh
creation and GLB export/import round trip. Private databases, personal browser
sessions, application projects and model weights are not opened. A Blender
Python check does not verify its MCP addon.

The 132-entry matrix uses explicit statuses: passed (stated operation verified),
partial (some reported operations passed), pending (setup/authorization or a
test is still needed), unavailable (the attempted check failed from this
environment), excluded (outside the no-payment default). An HTTP 403/429,
timeout or blocked network does not prove that the service itself is broken.

The last report stays in this project's private `.ai/` state. Harnesses can use
`list_integration_checks`, resource `swarm://hub/integration-checks`, or the CLI
to fetch/filter it on demand. Full matrices are not injected into startup
context and never ship inside portable exports. A new project starts with no
machine results. Use `docs/CREDENTIALS.md` and each selected `free-tool ID` for
remaining keys, OAuth/account steps, installation and application addon setup.

Checks replace evidence only for the scopes explicitly requested. Earlier
API, local application and external MCP results retain their original dates
when not retested; each retained row is labeled. A hub-only check therefore
keeps previously verified external functions without claiming a fresh test.
The CLI returns exit code 1 if the hub's own functional check fails. Pending
setup and optional provider failures remain explicit entries in the matrix.

External MCP tool calls require the real harness's permissions and an explicit
server connection. Before installing or connecting a third-party server, use
the available MCP precheck workflow and inspect its source, current package
version and tool scopes. The catalog and diagnostics do not proxy tools or
silently enable servers. Local test evidence can be attached to this project's
report through the trusted controller; distinguish tested functions from
untested functions even when initialize/tools-list succeeds.

The full source bundle includes `scripts/test_external_mcps.py` for Filesystem,
Memory, Git, Time, Fetch, Playwright and Chrome DevTools. After running the
current MCP precheck and resolving its decisions, invoke it explicitly:

```sh
python scripts/test_external_mcps.py --acknowledge-precheck --servers filesystem memory git time fetch playwright chrome --output tmp/external-mcp-results.json
```

This downloads server packages into workspace caches and launches temporary
stdio servers. Its JSON contains the actual discovered schemas/version and a
tested/pending status for each exposed function. It uses disposable Git/files
and an isolated headless Chrome browser; Fetch makes one public example.com
request. Memory's three deletion tools are denied by this test client. These
are not global harness deny rules. This script tests supported functions and
lists remaining functions explicitly, rather than claiming a full pass from
successful protocol initialization. Inspect any version/schema mismatch before
rerunning. No client configuration or global Git identity is changed.

The external test script returns exit code 1 for an unavailable server, failed
function validation or cleanup failure. Approved skipped Memory deletion tools
and discovery-only pending functions do not count as failed tests.
