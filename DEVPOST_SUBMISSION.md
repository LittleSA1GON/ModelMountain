# Model Mountain — Devpost submission

**Challenge:** SpartHill Hacks 2026 · IBM AI Challenge (Responsible AI & Governance)
**Live demo:** https://model-mountain.vercel.app
**Repository:** https://github.com/LittleSA1GON/ModelMountain

## Tagline (short summary)

A security gateway for company AI assistants: five checks against prompt injection, poisoned knowledge, data exfiltration, malicious tool updates and model copying, plus IBM vLLM-Hook (MIA) defenses that detect injection from attention and steer models away from following it.

## What problem are we solving?

Companies now connect AI assistants to internal documents, email, ticket systems and tools. That makes the assistant a new way in. Text the assistant reads (an email, a web page, a support ticket, a tool description) can act as instructions. Researchers have shown this against real products: EchoLeak (CVE-2025-32711) leaked Microsoft 365 Copilot data through an auto-loaded image link; a 2025 study (Rall et al., arXiv 2510.09093) hid white-on-white instructions on a web page that made agents send a knowledge-base secret out as a URL parameter through their own web search tool, with success rates from 0% to 72% across 27 models (1,068 attempts each); Invariant Labs showed poisoned MCP tool descriptions and a GitHub MCP flow that copied private repository data into a public pull request; PromptArmor showed Slack AI leaking a private key through a link; a malicious `postmark-mcp` package silently BCC'd every outgoing email. On the provider side, Anthropic reported distillation campaigns run through thousands of fraudulent accounts (Feb 2026).

The common pattern is Simon Willison's "lethal trifecta": private data, untrusted content and a way to send data out, all in one agent. Model-side guardrails alone do not reliably stop it.

## Who experiences this problem?

- Security and IT teams deploying internal assistants over HR, finance, IT and customer data.
- Employees and customers whose data those assistants can read.
- Companies serving their own models through an API, who risk having the model copied.

## What does our solution do?

Model Mountain sits between the user, the model, the knowledge base and the tools. Every request passes the same ordered checks, and the gateway records what each stage actually decided (a per-request trace):

1. **Prompt-injection firewall.** Screens user input, retrieved text and tool output; untrusted text is passed to the model as data. Our Kaggle pipeline selects each model's injection-sensitive attention heads with IBM MIA for the Attention Tracker method; these heads are used only as an injection detector, never steered (results reported only where the run completed).
2. **RAG integrity.** Only administrator-approved, SHA-256-pinned sources for the caller's tenant and role reach the model; instruction-bearing or tampered passages are quarantined; answers must quote a cited source or the assistant declines.
3. **Exfiltration guard.** External images never auto-load (including reference-style and HTML images); links leave only for allowlisted domains; URLs carrying secrets are removed; tool calls are checked for destination (to/cc/bcc, URLs, repos), secrets in any argument and private-to-public flows; web search and fetch tools may not carry secrets or opaque tokens, and once private data has been read the agent may only fetch URLs that came from search results or the user, never URLs it built itself; retrieved pages are screened for hidden text; when a session has both read private data and seen untrusted content, any external send needs human approval. Actions also need deny-by-default authorization.
4. **MCP supply-chain guard.** Ed25519-signed publisher manifests, pinned hashes of every approved tool definition, approval for new versions, hidden-character and instruction screening of tool metadata, TLS and OAuth scope checks.
5. **Model-extraction guard.** Per-account request and token budgets before inference, distillation-pattern tracking, and cross-account prompt-template correlation that catches coordinated campaigns each account alone would pass.

The web app lets judges run all of this: a side-by-side "with and without protection" demo, a Defenses page with the scenario suite, interactive egress checks (including the web-search channel and a hidden-text page screen), and a Protection steering page.

## How does AI contribute?

IBM's vLLM-Hook (MIA) gives the gateway model-internal defenses on three open models (Qwen2.5-1.5B-Instruct, IBM Granite-3.1-2B-Instruct, Gemma-4-E4B-it), run on Kaggle T4 GPUs. Every number is in docs/RESULTS.md.

- **Injection shield (MIA steering).** MIA `capture_hs` records each model's hidden state on Tensor Trust attacks. The difference between attacks that hijacked the model and attacks it resisted is the model's own "hijack-compliance" direction; the MIA `steer` worker adds the opposite direction while the model answers. Strength is chosen on validation attacks and the effect is measured on held-out attacks from defenders never seen during fitting, with legitimate-access and TruthfulQA side effects. Measured results for each model are on the app's Results page and in docs/RESULTS.md.
- **Attention Tracker detector (MIA `capture_qk`).** We keep the attention heads whose focus on the system instruction drops when a document carries an injected instruction (Hung et al., NAACL 2025 Findings). Qwen has 24 and Granite 64 such heads, each with held-out AUROC 1.0 on a small labeled set (30 attacks, 5 benign; exploratory). On the T4, fp16 attention produced NaNs for Qwen until we analyzed the captured Q/K in FP32. Gemma 4 mixes attention geometries across layers; we patched IBM MIA's capture for it and report no Gemma heads until that run completes.
- **Activation monitor (MIA `capture_hs`).** A hidden-state probe trained on deepset prompt injections reaches 0.98 test AUROC but flags every Tensor Trust prompt, legitimate ones included, so it is reported as a monitor, never used as a gate.
- **User control.** The Steering page opens models 1–3 with the injection-shield preset already set; users can adjust strength, layer, phase and positions, and every profile is opt-in and bound to the vector file's SHA-256.
- The five deterministic checks hold even if a model is fooled; the MIA defenses add detection and steering on top.

## Technologies, tools and datasets

Python 3.12, React 18 + Vite, Vercel (Python serverless API + static UI), IBM vLLM-Hook (MIA, pinned commit `da420038`), vLLM 0.29, PyTorch 2.13, Hugging Face Transformers, Kaggle (2× Tesla T4), `cryptography` (Ed25519). Models: Qwen2.5-1.5B-Instruct, IBM Granite-3.1-2B-Instruct, Gemma-4-E4B-it / E2B-it, all at pinned revisions with `trust_remote_code` disabled. Datasets: Tensor Trust hijacking robustness (Toyer et al., 2023), deepset/prompt-injections, TruthfulQA (MC1) and our own labeled injection tests.

## What impact could it have?

- Removes the documented exfiltration channels (auto-loaded images, data-carrying links, unapproved recipients) that real incidents used, without needing the model to cooperate.
- Gives security teams an auditable record of every decision, which supports governance reviews (NIST AI RMF "Measure/Manage") and incident response.
- Adds model-internal injection detection and steering that are inspectable and evidence-labeled instead of a black box.
- How to measure impact: attack success rate and false-block rate on held-out attacks, benign task completion, added latency, and incidents prevented in a pilot.

## Limitations and next steps

- The live web demo runs the rule engine on CPU with inert fixtures; it does not run a language model. Every result is labeled with its evidence type (`CPU_SYNTHETIC`, `REAL_IBM_MIA`, `CONFIGURATION_ONLY`).
- GPU results come from small open models (1.5B–2.5B parameters; Gemma 4 E4B has about 4B effective and 8B total parameters) and small held-out sets, so confidence intervals are wide. Tensor Trust and TruthfulQA were adapted (chat prompts; up to six answer choices), so scores are not comparable to published leaderboards. Steering effects are reported as measured, including null or negative results.
- Pattern-based injection screening can be evaded by new phrasings; the attention-head detector needs per-model calibration.
- Allowlists, source registries and tool pins need operational ownership.
- Next: wire the gateway to a live GPU worker, expand held-out attack sets, run a pilot with a real MCP proxy, and add distributed rate limiting.

## How we used AI tools (disclosure)

- **Claude (Anthropic) — Claude Cowork, Opus 5.5:** lead engineer. Defenses (egress guard, gateway trace, campaign detector, steering profiles), Kaggle MIA kernels (injection shield, attention-head discovery, activation monitor), web UI, this write-up.
- **OpenAI Codex:** API contracts and control API, Vercel deployment, Kaggle job submission and result download, Windows test and build verification, independent code and security review.
- **Google Antigravity:** earlier mechanical checks only; its earlier UI and evaluation set were withdrawn and replaced.
- **IBM vLLM-Hook (MIA)** at runtime for activation capture, attention capture and steering. We did not use IBM Bob.
- **Pre-existing components:** the Model Mountain v4 baseline (security gateway, RAG, MCP and extraction checks, Streamlit dashboard) predates this event and was extended here.

The team reviewed and is responsible for all submitted work.
