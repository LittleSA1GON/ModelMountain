# Model Mountain v3 release notes — October 23, 2026

## Added
- Unified gateway orchestrating five enterprise security areas in one request path.
- IBM MIA Qwen2-1.5B `MiaLLM` + Q/K Attention Tracker runtime adapter with a genuine `score` requirement.
- Optional model-specific risk-policy calibration, with a score-direction check and fail-closed model matching.
- Fail-closed behavior for missing MIA telemetry, tool-policy denial, input injection, poisoned or unauthorized retrieval, MCP trust failures, output secrets and extraction request-budget failures.
- Integrated CPU smoke-test report and new notebook real-gateway test mode.
- Test coverage for all new security gates, total **66 unit/integration tests passed** on CPU.

## Evidence status
- Unit tests: 66 passed.
- Self-contained notebook: executed successfully with real-MIA switch **off**.
- GPU IBM MIA inference: **NOT VERIFIED** in this environment.
- Activation steering improving security: **NOT DEMONSTRATED**; optional research direction, not an enabled prevention rule.
- Actual MCP network/production tool actions: **NOT IMPLEMENTED**, deliberately simulated.
- Five-area synthetic scenario test: 6 examples; 4 deny, 2 allow, no real agent tool execution.

## Important constraints
- MIA does not validate certificates, publisher signatures, OAuth, document authorization or model extraction budgets.
- Real attention gate requires independently calibrated and held-out-validated scores.
- The Qwen2-1.5B worker is the only integrated real-MIA model candidate; older multi-model benchmark is included separately.
- Do not deploy to businesses without production identity, egress, telemetry, storage, tested callback/tool isolation and high-quality evaluation.
