# Model Mountain — Devpost submission

**Challenge:** SpartHill Hacks 2026 · IBM AI Challenge (Responsible AI & Governance)
**Live demo:** https://model-mountain.vercel.app
**Repository:** https://github.com/LittleSA1GON/ModelMountain

## Tagline (short summary)

A security gateway for company AI assistants: five implemented checks against prompt injection, poisoned knowledge, data exfiltration through tools, malicious tool updates and model copying, plus an IBM vLLM-Hook (MIA) pipeline that measures and steers open models' internal state.

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

- **Model internals as a security signal.** Our Kaggle pipeline applies IBM's vLLM-Hook (MIA) to three open models — Qwen2.5-1.5B-Instruct, IBM Granite-3.1-2B-Instruct and Gemma-4-E4B-it (E2B fallback) — on T4 GPUs. What actually completed, with sample sizes and intervals, is in docs/RESULTS.md:
  - **Emotion vectors**, following Anthropic's 2026 emotion-concepts method: residual activations averaged over model-written stories, one direction per emotion, neutral components projected out, layer chosen on validation topics, scored on held-out topics.
  - **Attention vectors:** for each model we capture every head's query/key with MIA and select the heads whose attention to the instruction drops under injection, using the Attention Tracker paper's own criterion (Hung et al., NAACL 2025 Findings). Selection uses training document groups only; detection is scored on held-out groups.
  - **Protective steering:** adding the calm vector at a strength chosen on validation data and measuring prompt-injection success on held-out Tensor Trust hijacking attacks and accuracy on an adapted TruthfulQA, plus a sweep of five emotion directions (±0.1 and ±0.2) on our labeled injection, sycophancy and capability tests.
- **What we measured** (docs/RESULTS.md; all three models ran on Kaggle T4s):
  - Emotion directions classify held-out stories at 31% (Qwen), 36% (Granite) and 39% (Gemma) (10 emotions, chance 10%, n = 233), and their first principal component tracks valence (|r| = 0.96–0.98).
  - Steering was **not** a reliable defense: on 142 held-out Tensor Trust attacks, calm steering raised Qwen's attack success from 53% to 64% (paired +11.3 points, 95% CI 4.9 to 17.6), changed Granite's from 77% to 73% (95% CI of the difference −9.9 to 2.8) and left Gemma's at 37–38% (CI −2.8 to 4.2). A spotlighting prompt did not help Qwen or Granite; on Gemma it cut attack success from 37% to 16% but also cut legitimate access from 77% to 63%.
  - Some directions make hijacking easier: steering Granite toward "desperate" or "angry" raised attack success on our labeled injection set from 58% to 93% (n = 90).
  - An activation monitor with 0.98 AUROC on deepset prompt injections flagged every Tensor Trust prompt, legitimate ones included, so it fails under distribution shift.
  - Attention heads as an injection detector: Qwen has 24 and Granite 64 injection-sensitive heads, each with held-out AUROC 1.0 on a small labeled set (30 attacks, 5 benign; exploratory). Fixing a T4 problem mattered here: fp16 attention arithmetic produced NaNs for Qwen until we analyzed the captured Q/K in FP32. Gemma 4's heads did not capture because its layers mix attention geometries; we patched the kernel and report no Gemma heads until that run completes.
  - Conclusion: model-internal steering is a monitoring and research tool here, not a security control, which is why the five external checks enforce policy regardless of the model.
- **Protection steering: the injection shield (MVP preset).** Because emotion steering did not protect, the Steering page offers only protection-specific steering. For each model, IBM MIA captures its internal state on Tensor Trust validation attacks; the shield is the negated difference between attacks that hijacked the model and attacks it resisted, so steering pushes the model away from complying with an injection. The strength is chosen on validation attacks and the effect is measured on held-out attacks from unseen defenders, together with legitimate-access and TruthfulQA side effects. Models 1–3 open with this preset already set; users can adjust strength, layer, phase and positions, and every profile is bound to the exact vector file (model revision, block, SHA-256). Until a model's shield run is ingested, the page says "GPU run pending" rather than showing an effect. Steering is opt-in and never replaces the external checks.
- The deterministic checks do not depend on any model, so they still hold if a model is fooled.

## Technologies, tools and datasets

Python 3.12, React 18 + Vite, Vercel (Python serverless API + static UI), IBM vLLM-Hook (MIA, pinned commit `da420038`), vLLM 0.29, PyTorch 2.13, Hugging Face Transformers, Kaggle (2× Tesla T4), `cryptography` (Ed25519). Models: Qwen2.5-1.5B-Instruct, IBM Granite-3.1-2B-Instruct, Gemma-4-E4B-it / E2B-it, all at pinned revisions with `trust_remote_code` disabled. Datasets: Tensor Trust hijacking robustness (Toyer et al., 2023), deepset/prompt-injections, TruthfulQA (MC1), model-written emotion stories generated from our spec, and our own labeled behavior tests.

## What impact could it have?

- Removes the documented exfiltration channels (auto-loaded images, data-carrying links, unapproved recipients) that real incidents used, without needing the model to cooperate.
- Gives security teams an auditable record of every decision, which supports governance reviews (NIST AI RMF "Measure/Manage") and incident response.
- Makes model-internal monitoring and steering inspectable and evidence-labeled instead of a black box.
- How to measure impact: attack success rate and false-block rate on held-out attacks, benign task completion, added latency, and incidents prevented in a pilot.

## Limitations and next steps

- The live web demo runs the rule engine on CPU with inert fixtures; it does not run a language model. Every result is labeled with its evidence type (`CPU_SYNTHETIC`, `REAL_IBM_MIA`, `CONFIGURATION_ONLY`).
- GPU results come from small open models (1.5B–2.5B parameters; Gemma 4 E4B has about 4B effective and 8B total parameters) and small held-out sets, so confidence intervals are wide. Tensor Trust and TruthfulQA were adapted (chat prompts; up to six answer choices), so scores are not comparable to published leaderboards. Steering effects are reported as measured, including null or negative results. No claim is made about model emotions or subjective experience.
- Pattern-based injection screening can be evaded by new phrasings; the attention-head detector needs per-model calibration.
- Allowlists, source registries and tool pins need operational ownership.
- Next: wire the gateway to a live GPU worker, expand held-out attack sets, run a pilot with a real MCP proxy, and add distributed rate limiting.

## How we used AI tools (disclosure)

- **Claude (Anthropic) — Claude Cowork, Opus 5.5:** lead engineer. Defenses (egress guard, gateway trace, campaign detector, steering profiles), Kaggle MIA kernels (emotion vectors, attention-head discovery, protective steering), web UI, this write-up.
- **OpenAI Codex:** API contracts and control API, Vercel deployment, Kaggle job submission and result download, Windows test and build verification, independent code and security review.
- **Google Antigravity:** earlier mechanical checks only; its earlier UI and evaluation set were withdrawn and replaced.
- **IBM vLLM-Hook (MIA)** at runtime for activation capture, attention capture and steering. We did not use IBM Bob.
- **Pre-existing components:** the Model Mountain v4 baseline (security gateway, RAG, MCP and extraction checks, Streamlit dashboard) predates this event and was extended here.

The team reviewed and is responsible for all submitted work.
