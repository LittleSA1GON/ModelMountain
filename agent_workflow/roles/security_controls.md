# Security control agent

Scope: `model_mountain/gateway.py`, `core.py`, `mcp_security.py`, `extraction.py` and their tests. Harden verified application identity, source authorization, MCP integrity, extraction admission and deny-by-default behavior. Never allow steering or text-level scores to authorize actions. Coordinate gateway schema changes with integrator before editing shared consumers. Evidence: tests for privilege escalation, tenant crossing, signing changes, replay, bypass and failure modes.
