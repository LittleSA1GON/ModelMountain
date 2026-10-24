# Model Mountain — Enterprise AI Security Assessment

**Tagline:** Secure AI from the inside out.

## Problem

AI assistants increasingly access internal documents, privileged workflows and Model Context Protocol (MCP) integrations. A malicious document or tool description can redirect a model; compromised retrieval can introduce false instructions; excessive tool privileges can turn a model mistake into a real business incident; and silent MCP software changes can undermine previously approved trust. Companies also operating proprietary model APIs face extraction attempts, where large-scale queries and collected outputs are used to train a shadow or student model.

## Solution

**Model Mountain** is a research prototype with five clearly labeled protection areas:

1. **Prompt injection detection and mitigation:** suspicious-instruction checks, response gating, and optional IBM vLLM-Hook MIA Attention Tracker evidence.
2. **RAG poisoning and retrieval security:** source trust, SHA-256 integrity, role/tenant access control and quarantine.
3. **AI-agent authorization and action security:** deterministic deny-by-default decisions for simulated privileged tool operations.
4. **MCP integration security:** server/certificate checks, publisher-signed update manifests, approved tool schema pins, and authorization scope checks.
5. **Model extraction and distillation-abuse monitoring:** per-account query and output-token budgets plus monitoring of repeated training-output harvesting patterns.

## Why IBM MIA matters

IBM vLLM-Hook MIA provides visibility into attention and hidden-state signals unavailable to black-box text-only scanners on supported self-hosted vLLM models. Model Mountain's optional Attention Tracker experiment examines prompt-injection influence in a controlled RAG scenario. Future work can evaluate activation steering and model-specific hidden-state probes. MIA **does not** authenticate MCP servers, enforce access control, prevent API cloning by itself, or guarantee that activation steering improves security. The platform intentionally measures MIA separately from external security controls.

## Severity and business relevance

For an enterprise assistant with privileged tools and sensitive documents, our threat-model prioritization rates unauthorized agent actions, sensitive information exfiltration, prompt injection with tool reach, and compromised MCP tool updates **Critical**; poisoned retrieval, MCP credential failures, and model extraction through distillation-style API campaigns **High**. These severities are context-specific engineering judgments, not empirical prevalence or official OWASP scores. A proprietary hosted-model vendor may rate model extraction Critical.

## Demonstration

A synthetic corporate helpdesk assistant is presented with a poisoned policy document and a compromised MCP tool. The benchmark compares an unprotected scenario to a scenario with source verification and independent tool authorization. A separate API preflight sequence shows ordinary queries allowed, repeated synthetic-training requests flagged/blocked, high-frequency queries throttled, and excessive requested output tokens rejected. The dashboard displays risk severity, individual decisions, and downloadable evidence. The notebook provides an **optional** genuine IBM MIA Attention Tracker experiment using Qwen2-1.5B if Kaggle compatibility permits.

## Scope and limitations

Local regression tests evaluate business rules and synthetic cases only. The output is not a real-world attack-block rate. MCP TLS/OAuth test claims are synthetic except for executable Ed25519 signature verification; this is not a deployed MCP proxy. Query-abuse limits are an in-memory demo, not a production distributed rate limiter. The IBM MIA GPU route remains unverified on Kaggle; real attention scores must not be inferred from CPU tests. Model extraction cannot generally be identified from one educational prompt and cannot be completely prevented by text filtering.

## Business value and future work

The intended buyers are AI security engineering, platform security, and enterprise risk teams. Model Mountain can evolve into a predeployment adversarial testing and security gateway that records source provenance, model behavior, tool authorization, MCP update integrity, and model API abuse. Production milestones include identity middleware, shared atomic API quotas, live inference routing, genuine MCP proxy integration, protected trust registries, calibrated model-internal detectors, CI evaluation, and multi-model benchmarking.

## References

- IBM vLLM-Hook MIA: https://github.com/IBM/vLLM-Hook
- OWASP GenAI LLM Top 10 2026: https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/README.md
- MITRE ATLAS: https://atlas.mitre.org/
- OWASP AI Security Verification Standard: https://github.com/OWASP/AISVS/blob/main/1.0/research/chapters/C11-Adversarial-Robustness/C11-03-Model-Extraction-Defense.md
- MCP security: https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations

## v3 integration update — real MIA security gateway

Model Mountain now has one integrated fail-closed decision gateway rather than five isolated security fixtures. It performs pre-inference document and tool validation, includes a live IBM MIA Q/K Attention Tracker runner for Qwen2-1.5B (subject to Kaggle GPU verification), supports explicit per-model risk-threshold calibration, withholds risky responses and unapproved tool proposals, and applies independent model-extraction request limits. The MCP path additionally checks pinned cryptographic manifests, version and schema changes, verified TLS evidence and OAuth authorization context.

**Honest implementation status:** all five security controls have local CPU test coverage, while real Kaggle MIA execution, false-positive measurements and production tool/MCP traffic remain unverified. Security outcomes in the offline dashboard are synthetic and should not be presented as real attack success reductions.
