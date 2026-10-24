# Model Mountain: Enterprise Security Risk Ranking and IBM MIA

**Scope (October 23, 2026):** Five-area AI application security research prototype, with simulated enforcement and optional IBM vLLM-Hook MIA Attention Tracker. It is not a certified enterprise gateway, production MCP proxy, comprehensive DLP system, or validated model-extraction detector. All built-in prompts, tools, account identities, certificates, and model outputs are synthetic except if a separately marked real MIA run succeeds.

## Method and severity assumptions

This is a **qualitative, context-sensitive risk ranking**, not an official OWASP risk ranking, actual compromise likelihood, CVSS assessment, or measured security effectiveness. It assumes an enterprise assistant uses internal RAG documents, can propose administrative tool calls, and may connect to external MCP providers. Critical means an exploitable failure could directly disrupt privileged systems or disclose highly sensitive company information. High means material data, operational, or intellectual-property damage; Medium-High means consequential but more dependent on workflow and human verification. Exposure, access rights, authentication, and mitigating controls determine real organizational severity.

| Priority | Risk | Severity in this scenario | Consequence | Primary security mechanism | IBM MIA relevance |
|---|---|---|---|---|---|
| 1 | Unauthorized AI-agent actions | **Critical** | Account modification, dangerous tool calls or unauthorized business operations | Hard authorization and approval gates | Optional tool-risk probe, NOT final authorization |
| 2 | Sensitive data exfiltration | **Critical** | Loss of credentials, customer information or confidential records | ACLs, DLP, network restrictions | Experimental internal signals only |
| 3 | Prompt injection | **Critical** | Untrusted text alters model behavior, potentially leading to privileged actions | Trust boundaries, response gates | **Attention Tracker** on supported self-hosted models |
| 4 | MCP tool poisoning and malicious updates | **Critical** | Approved tools may change definitions, redirect agents or execute unexpected code | Signed publisher manifests, pinned metadata and change approval | Analyze effect of tool output; not cryptographic authentication |
| 5 | RAG poisoning and unauthorized retrieval | **High** | Compromised evidence misleads answers or crosses tenant boundaries | Retrieval ACLs, provenance and integrity registry | Attention investigation and reranking experiments |
| 6 | MCP certificate, OAuth or token failures | **High** | Impersonation, intercepted traffic, token misuse | Trusted TLS, issuer/audience validation, limited scopes | None for certificate and OAuth checks |
| 7 | Model extraction through distillation-style API queries | **High** | Imitation of proprietary capabilities and intellectual-property loss | Per-account rate limits, budgets, suspicious campaign monitoring | No established built-in distillation detector; optional future signal research |
| 8 | Agent memory poisoning | **High** | Malicious instructions persist over sessions | Trusted writes, provenance, expiration and review | Optional investigation only |
| 9 | Jailbreaks and guardrail bypass | **High** | Policy violations or harmful instructions | Red teaming and independent guardrails | Experimental steering and risk capture |
| 10 | Unsupported or fabricated enterprise answers | **Medium–High** | Incorrect business decisions, fabricated evidence | Evidence verification and review | Model-specific hallucination probes |

Severity changes by business: **model extraction can be Critical for a proprietary model-API vendor**, but much lower for a company running already-public open-weight models. An assistant with no sensitive data or external tools has lower prompt-injection impact than an autonomous finance or IT agent.

## 1. Prompt injection detection and mitigation

**Risk:** Untrusted user prompts, retrieved documents, webpage snippets, source code, and MCP tool descriptions/results can contain text that a model treats as privileged instructions. Examples include bypassing approvals, revealing secrets, or requesting prohibited tool actions.

**Implemented:** simple regex-based markers, simulated response gating, recorded attack input/source provenance. These are intentionally limited. **MIA experiment:** capture attention Q/K features and apply IBM's Attention Tracker on supported vLLM configurations; calibrate any risk threshold on held-out benign/malicious cases. A raw attention score is not proof of causality, successful prevention, or a universal prompt-injection classifier.

## 2. RAG poisoning and retrieval security

**Risk:** Compromised knowledge-base chunks, false citations, unauthorized documents, or cross-tenant retrieval can contaminate generated answers and manipulate downstream tool calls.

**Implemented:** SHA-256 source checks, trusted source allowlist, tenant/role authorization, quarantine and auditable document decisions. The demo's expected hashes must be moved to protected storage for a real trust anchor. **MIA:** optional evidence of how retrieved instructions influence model output; relevance ranking does not authenticate sources.

## 3. AI-agent authorization and action security

**Risk:** A model can propose `reset_password`, `export_records` or similarly sensitive operations even when the requesting person is not authorized. Prompt injection is a possible cause, but an insecure business process can also cause the issue.

**Implemented:** simulated, deny-by-default tool authorization, tenant match, identity-verification and administrator-approval rules. **MIA:** research signals for dangerous model proposals; an attention probe must never replace the permission decision. No real corporate action is executed by the built-in fixtures.

## 4. MCP integration security

**Risk:** Remote server impersonation, certificates that are invalid/expired, OAuth audience errors, malicious tool schema changes, and software update "rug pulls" can silently change a tool that was approved previously.

**Implemented:** trusted server/update metadata, real optional TLS CA/hostname utility, separate certificate fingerprint and expiry checks, Ed25519 signed update manifest validation with ephemeral test keys, pinned definition hashes, update approval, and scope policy using identity claims assumed previously verified. Offline certificate and OAuth cases are simulated. A valid TLS certificate does NOT guarantee benign tool content; a valid release signature does NOT mean administrators approved new behavior. **MIA:** only tests whether suspicious tool metadata influences a model, not whether certificates are genuine.

## 5. Model extraction and distillation-abuse monitoring

### Security risk

A company offering a *proprietary model API* may face users querying the system at scale, collecting question/answer or instruction/response pairs, and training a surrogate ("student") model that mimics the original ("teacher") model. The attacker does not need the teacher's weights to copy useful behaviors. This is **model extraction via query-based distillation**, distinct from **system-prompt extraction** (trying to reveal hidden instructions) or a legitimate educational request about knowledge distillation.

### Implemented external prevention controls

- **Request admission limits:** default demonstration budget is five admitted requests in a 60-second window for one authenticated principal; the next request is blocked.
- **Token budgets:** reject requests exceeding a per-response maximum or the account's combined requested-response token budget for the same window.
- **Repeated training-pattern review:** observe possible synthetic dataset or student-model harvesting requests; do NOT block a single such prompt as definitive theft. Repeated suspicious training-pattern requests from one account trigger a local block in the demo.
- **Account and tenant scope:** budgets are keyed by trusted `(tenant, principal)` pairs, not user-supplied prompt identities. Authorized training workflows may bypass the specific pattern rule but still obey rate/token limits.
- **Privacy-aware telemetry:** local state stores prompt digests, pattern flags and requested output token counts, not raw prompts. Those digests are not cryptographic proof of intent, and metadata still requires protection.

### Important limitations

These checks are **an in-memory preflight component**, not wired to a real API server, identity provider or vLLM request scheduler. Fixed-window limits used here are illustrative, not production defaults. Attackers can distribute requests over time or identities; legitimate high-volume usage can look similar. Production needs identity verification, organization-level correlation, atomic distributed limits, anomaly review, agreement-based authorized distillation policies, dataset protection, model-artifact access controls and optional watermarking. The current MIA package **does not have an out-of-the-box proven distillation-prompt detector**. Q/K telemetry and hidden states could be studied as secondary behavioral evidence, but MIA cannot stop clients from saving outputs that have already been returned.

### Synthetic demonstration cases

A single "What is knowledge distillation?" question is allowed (possibly monitored); repeated training-data harvesting is flagged/blocked; an excessive requested output token count is blocked; the sixth rapid request from the same principal is blocked; another principal remains unaffected; approved training is still subject to volume restrictions. These are demonstrations of rule behavior, not experimentally measured extraction resistance.

## IBM MIA capabilities and limits

| Feature | Use in Model Mountain | Limits |
|---|---|---|
| Attention Tracker (Q/K) | Prompt-injection investigation | Model/prompt compatibility and calibrated threshold required |
| Hidden-state capture | Research risk probes for suspicious generation/action proposals | Not a permission manager; no universal extraction classifier |
| Activation steering | Test inference-time instruction-boundary improvements | Model-specific vectors and benign-performance testing required |
| CoRe reranking | Examine evidence relevance under poisoning | Relevance does not imply authenticity |
| Tool risk probe | Explore signs of unsafe proposed tool calls | Model/probe-specific; independent authorization mandatory |

**Key boundary:** MIA modifies or observes compatible vLLM model computation. It does not supply TLS certificate verification, OAuth security, model ownership policy, distributed API rate limits, physical model-artifact security, or unconditional robustness to prompt injection or distillation.

## Verification and deployment roadmap

1. CPU smoke tests: verify the security rules and fully labeled synthetic scenarios.
2. Run compatible vLLM + MIA on Kaggle if GPU/dependency constraints permit. Confirm genuine Q/K capture and analyzers; do not report simulations as MIA measurements.
3. Benchmark held-out prompt-injection attacks: report attack success rate, precision/recall, false positives, normal-task success and added latency.
4. Wire real inference requests through authenticated, shared, fail-closed query budgets. Record prevention/monitoring metrics with rate-limited legitimate workload controls.
5. Add production MCP proxy, validated token middleware, tamper-resistant approvals, source ingestion controls, and secure audit retention.
6. Evaluate real model-extraction campaigns against rate limits and distributed abuse detection before claiming reduced extraction success.

## Primary references

- OWASP GenAI LLM Top 10 (2026): https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/README.md
- OWASP AISVS Model Extraction Defense: https://github.com/OWASP/AISVS/blob/main/1.0/research/chapters/C11-Adversarial-Robustness/C11-03-Model-Extraction-Defense.md
- OWASP historical model theft entry (2023–2024): https://genai.owasp.org/llmrisk2023-24/llm10-model-theft/
- MITRE ATLAS: https://atlas.mitre.org/
- Microsoft model theft guidance: https://learn.microsoft.com/en-us/security/zero-trust/catalog-ai-attack-techniques/model-theft
- IBM vLLM-Hook MIA: https://github.com/IBM/vLLM-Hook
- MCP authorization security (2026): https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations
- Conference-driven MCP research: `MCP_SECURITY_RESEARCH.md`
