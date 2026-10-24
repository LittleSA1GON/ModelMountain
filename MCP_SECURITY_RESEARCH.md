# MCP security: AGNTCon + MCPCon 2026 research and implementation notes

Research date: October 23, 2026. Source basis: publicly published **session descriptions**, not firsthand transcripts or claims that a session's demonstrations were independently audited.

## Sources and design decisions

1. **MCP Rug Pulls in the Wild: Live Attacks and How to Stop Them** (Advait Patel and Charit Upadhyay, Oct 22, 3:30–3:55pm) described malicious changes to tool definitions after approval and presented cryptographic tool identity, definition-change detection, and runtime monitoring. Source: https://events.linuxfoundation.org/agntcon-mcpcon-north-america/program/schedule/?topic=mcpcon .
   - Implemented: SHA-256 hashes of each MCP tool's full model-facing metadata, an approved baseline, fail-closed comparison every assessment, signed publisher manifest, explicit admin approval on version/update changes and changed package artifact digests.
2. **MCP Security, Two Years In** (Den Delimarsky, Oct 22, 2:20–2:45pm) described OAuth issuer/server-bound credentials, verifiable clients, consent, and untrusted tool output. Same schedule source.
   - Implemented: gate consuming *already verified* OAuth context from trusted middleware, with exact issuer, audience and per-tool scope checks. The prototype does NOT implement an OAuth server or independently verify JWTs.
3. **Rethinking CI/CD Release Gates for Agent-native Software** (Prathmesh Patel, Oct 22, 11:10–11:35am) proposed checks for behavior, protocol/OAuth compliance, deterministic failures, and poisoning/prompt injection. Same schedule source.
   - Implemented: synthetic security regression suite and signed-manifest/version gating. No full MCP conformance tester is included.
4. **Workshop: Governing Enterprise AI Agents: Tools, Exploits & Prompt Injection** (Shannon Williams and Bill Maxwell, Oct 23, 1:45–3:20pm) discussed managed registries, least privilege, unapproved servers, tool poisoning, rug pulls, and gateway audits. Source: https://events.linuxfoundation.org/agntcon-mcpcon-north-america/program/schedule/?topic=mcpcon .
   - Implemented: explicit allowlist of known MCP server identity/endpoint/publisher, per-tool scope and action checks, tests for shadow MCP servers.
5. **The 2026-07-28 MCP specification** introduced stateless request flow, cacheable `tools/list` with `ttlMs`, header-based routing, issuer (`iss`) validation, and changes to client metadata registration. Source: https://blog.modelcontextprotocol.io/posts/2026-07-28/ .
   - Engineering requirement: revalidate tool metadata when a fresh list arrives and prior to a privileged call. `ttlMs` is a cache hint, not a security approval. In a real gateway validate OAuth `iss` and token audience with the trusted OAuth library.
6. **MCP Tools specification** recommends human ability to reject calls; tools/list content can change over time. Source: https://modelcontextprotocol.info/specification/2026-07-28/server/tools/ .

## Certificates: three concepts to distinguish

- **TLS/X.509 certificates:** HTTPS server authenticity and encrypted channel; `verify_remote_tls()` creates a CA-verifying, hostname-checking `ssl` client and returns certificate fingerprint plus expiry metadata. `certificate_expiry_status()` distinguishes expired and soon-to-expire certificates, with a configurable renewal warning interval. The offline Kaggle demo does NOT establish a real TLS connection. For live production, an egress proxy and DNS rebinding protection are also required.
- **Publisher signing keys:** Ed25519 digital signatures over a canonical JSON manifest binding server identity, endpoint, software version, package artifact digest, and every tool-definition hash. A genuine signature says a trusted key approved *these bytes*, not that they are harmless. This is **Model Mountain's own signed-manifest format**, not an MCP-protocol-mandated certificate/attestation standard. The demo uses an ephemeral signing key and never ships private production keys.
- **MCPA professional certification:** The Linux Foundation/Agentic AI Foundation's Model Context Protocol Associate credential certifies a person's MCP knowledge; it does **not** authenticate an MCP server or sign a tool update. Source: https://www.linuxfoundation.org/press/agentic-ai-foundation-launches-mcpa-certification-to-validate-mcp-expertise .

## Required security behavior on MCP updates

- Fail closed if an approved tool's `description`, name, input/output schema, or annotations changes unexpectedly — even if the server version string stays the same.
- Fail closed when package artifact hash changes without an approved signed manifest and explicit administrative promotion.
- Verify the publisher signature against a previously trusted pinned public key; do not auto-trust a key supplied by the same untrusted MCP server.
- Do NOT auto-promote an update merely because it has a valid signature. Obtain explicit review and rerun validation; newly added tools require separate scope review.
- For optional TLS **leaf certificate pinning**, rotate pins via trusted administrative review. Many legitimate certificate renewals change the leaf digest, so use standard CA/hostname validation as a baseline, not automatic global pinning.
- Validate OAuth issuer, intended audience/resource, and tool scopes using a genuine, authenticated identity provider; never accept text-supplied claims as verification.
- Treat `tools/list` and tool outputs as untrusted data. IBM MIA can study prompt-injection influence; it CANNOT authenticate TLS, verify package signatures, or enforce OAuth.

## Implemented files and evidence

- `model_mountain/mcp_security.py`: pure-Python preflight gate with optional `cryptography` for Ed25519 verification, opt-in real TLS verification, synthetic test suite, update-approval helper and an MCP and agent-authorization combined decision.
- `tests/test_mcp_security.py`: validation tests, including poisoned definitions, certificate changes, malformed signatures, identity/authorization failures, and update approval.
- `app.py`: MCP security tab with a clearly labeled simulated incident dashboard.
- `model_mountain/cli.py`: exports `mcp_report.json` and an HTML summary alongside the original report.
- `Model_Mountain_IBM_MIA_Kaggle.ipynb`: self-contained project with all five protection areas; the genuine IBM MIA run is *still optional and not validated on Kaggle GPU*.

## Engineering limitations (not production-ready)

This is a defensible **MVP preflight implementation**, not a transparent, full-featured MCP proxy. It does not itself query remote `tools/list`, run MCP `tools/call`, implement OAuth login or verify JWT signatures, scan binaries with an antivirus, prove supply-chain provenance, enforce system network egress or persist a protected admin-approved registry. `TLSResult` and `MCPVerifiedAuth` MUST be produced by trusted middleware. The explicit `SIMULATED_TEST_ONLY` input mode is rejected by default. The tool action helper returns a simulated decision; it never executes external tools. Before real enterprise adoption, integrate these checks with a real MCP client/gateway, secure signed registry and administrative workflows, certificate rotation alerts, OAuth/OIDC verification, identity-aware policy, monitoring, and package provenance tooling (e.g. Sigstore/SLSA).
