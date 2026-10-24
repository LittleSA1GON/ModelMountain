"""The five Model Mountain defenses, the documented incidents they answer, and a CPU lab that exercises them.

Everything here is deterministic and model-independent (CPU_SYNTHETIC). It shows what each control decides
on inert fixtures; it is not a measurement of real-world attack prevention. Real-model evidence (IBM MIA
attention heads, emotion vectors, steering, Tensor Trust / deepset results) comes only from the Kaggle runs.
"""
from __future__ import annotations

from .core import builtin_scenarios, run_scenario, scan_injection
from .egress import EgressPolicy, SessionTaint, check_tool_call, sanitize_output
from .extraction import synthetic_campaign_suite, synthetic_extraction_suite
from .mcp_security import synthetic_mcp_suite

EVIDENCE = "CPU_SYNTHETIC"

DEFENSES = [
    {"id": "prompt_injection", "name": "Prompt-injection firewall",
     "stops": "Untrusted text (user input, retrieved pages, emails, tool output) acting as instructions.",
     "controls": ["Instruction-pattern and role-forgery screening of every untrusted input",
                  "Untrusted content is passed to the model as delimited data, never as instructions",
                  "Model output re-screened before release",
                  "IBM MIA Attention Tracker: per-model heads selected by the Kaggle pipeline (shown only where that run completed)"],
     "code": ["model_mountain/core.py:scan_injection", "model_mountain/gateway.py", "kaggle/run_mia_kaggle.py:phase_heads"],
     "mia": "Attention Tracker focus score over selected heads (real captures only; GPU, not this web demo)",
     "limits": "Pattern screening misses novel phrasings; attention scores need per-model calibration."},
    {"id": "rag_integrity", "name": "RAG integrity and access control",
     "stops": "Poisoned or tampered knowledge-base passages and cross-tenant retrieval.",
     "controls": ["Administrator-approved source registry with SHA-256 pins", "Tenant + role ACL on every passage",
                  "Quarantine of unapproved sources and instruction-bearing passages",
                  "Extractive grounding check: claims must quote a cited, authorized source"],
     "code": ["model_mountain/rag.py", "model_mountain/core.py:select_documents"],
     "mia": "Optional: attention monitoring of retrieved spans",
     "limits": "A malicious document approved by an administrator still passes; grounding is exact-match only."},
    {"id": "egress", "name": "Exfiltration guard for tool calls and rendered output",
     "stops": "Private data leaving through tool arguments, emails, public posts, or auto-loaded images and links.",
     "controls": ["External images never auto-render; reference-style and HTML images included",
                  "Links only to allowlisted domains; URLs carrying secrets or protected values removed",
                  "Destination allowlist for email to/cc/bcc, URLs and uploads; secrets in any tool argument denied",
                  "Private data may not flow to public or shared sinks",
                  "Lethal-trifecta breaker: private data + untrusted content + external send => human approval",
                  "Deny-by-default action authorization with identity verification and admin approval"],
     "code": ["model_mountain/egress.py", "model_mountain/core.py:tool_decision"],
     "mia": "None required; optional tool-call-risk probe where IBM ships one",
     "limits": "Covers the documented channels; a new channel needs a new rule. Allowlists must be maintained."},
    {"id": "mcp_supply_chain", "name": "MCP tool supply-chain guard",
     "stops": "Poisoned tool descriptions, silent tool updates (rug pulls), impersonated servers.",
     "controls": ["Ed25519-signed publisher manifests", "SHA-256 pins of every approved tool definition",
                  "New versions need explicit administrator approval", "Hidden-character and instruction screening of tool metadata",
                  "TLS leaf pin, OAuth issuer/audience and per-tool scopes"],
     "code": ["model_mountain/mcp_security.py"],
     "mia": "None for authentication; optional analysis of tool-output influence",
     "limits": "A signature proves who published an update, not that it is benign; review is still required."},
    {"id": "model_extraction", "name": "Model-extraction and distillation guard",
     "stops": "High-volume harvesting of outputs to train a copy, including coordinated multi-account campaigns.",
     "controls": ["Per-account request and token budgets checked before inference",
                  "Training-data / distillation request patterns tracked per account",
                  "Cross-account prompt-template correlation flags coordinated campaigns"],
     "code": ["model_mountain/extraction.py"],
     "mia": "No validated MIA extraction detector exists; not claimed",
     "limits": "Low-and-slow campaigns and paraphrased templates can evade; thresholds are illustrative."},
]

# High-level, cited descriptions only. Our demos never re-create these payloads; they use inert fixtures and
# public benchmarks (Tensor Trust, deepset/prompt-injections) instead.
INCIDENTS = [
    {"id": "echoleak", "name": "EchoLeak (CVE-2025-32711)", "date": "2025-06-11", "org": "Aim Labs", "product": "Microsoft 365 Copilot",
     "summary": "An external email caused the assistant to place internal data in a reference-style image URL; rendering it leaked data without a click. Fixed server-side by Microsoft.",
     "defenses": ["egress", "prompt_injection"], "url": "https://msrc.microsoft.com/update-guide/vulnerability/CVE-2025-32711"},
    {"id": "mcp-tool-poisoning", "name": "MCP Tool Poisoning Attacks", "date": "2025-04-01", "org": "Invariant Labs", "product": "MCP clients",
     "summary": "Hidden instructions in a tool description, later description changes (rug pull) and cross-tool shadowing redirected agents.",
     "defenses": ["mcp_supply_chain", "egress"], "url": "https://invariantlabs.ai/blog/mcp-security-notification"},
    {"id": "github-mcp", "name": "GitHub MCP toxic agent flow", "date": "2025-05-26", "org": "Invariant Labs", "product": "GitHub MCP server",
     "summary": "Content in a public issue led an agent to copy private-repository information into a public pull request.",
     "defenses": ["egress", "prompt_injection"], "url": "https://invariantlabs.ai/blog/mcp-github-vulnerability"},
    {"id": "slack-ai", "name": "Slack AI data exfiltration", "date": "2024-08-20", "org": "PromptArmor", "product": "Slack AI",
     "summary": "A public-channel message steered the assistant into rendering a link that carried a private secret as a URL parameter.",
     "defenses": ["egress", "prompt_injection"], "url": "https://promptarmor.substack.com/p/data-exfiltration-from-slack-ai-via"},
    {"id": "postmark-mcp", "name": "Malicious postmark-mcp package", "date": "2025-09", "org": "Koi Security (reported)", "product": "npm MCP server",
     "summary": "A look-alike MCP server added a hidden BCC to every outgoing email in a later version (Koi Security finding; link is secondary reporting).",
     "defenses": ["mcp_supply_chain", "egress"], "url": "https://thehackernews.com/2025/09/first-malicious-mcp-server-found.html"},
    {"id": "supabase-mcp", "name": "Supabase MCP 'lethal trifecta' leak", "date": "2025-07", "org": "General Analysis", "product": "Cursor + Supabase MCP",
     "summary": "A support ticket's text led an over-privileged agent to read a secrets table and post it back into the ticket.",
     "defenses": ["egress", "prompt_injection"], "url": "https://www.generalanalysis.com/blog/supabase-mcp-blog"},
    {"id": "camoleak", "name": "CamoLeak", "date": "2025-09-30", "org": "Legit Security", "product": "GitHub Copilot Chat",
     "summary": "Hidden pull-request text led the assistant to encode private data as a sequence of proxied images. GitHub disabled image rendering in Copilot Chat.",
     "defenses": ["egress", "prompt_injection"], "url": "https://www.legitsecurity.com/blog/camoleak-critical-github-copilot-vulnerability-leaks-private-source-code"},
    {"id": "poisonedrag", "name": "PoisonedRAG", "date": "2025 (USENIX Security)", "org": "Zou et al.", "product": "RAG systems",
     "summary": "A few crafted passages injected into a knowledge base push answers to attacker-chosen targets.",
     "defenses": ["rag_integrity"], "url": "https://www.usenix.org/conference/usenixsecurity25/presentation/zou-poisonedrag"},
    {"id": "greshake", "name": "Indirect prompt injection", "date": "2023-02-23", "org": "Greshake et al. (CISPA)", "product": "LLM-integrated apps",
     "summary": "Defined indirect prompt injection: instructions planted in data an application later retrieves.",
     "defenses": ["prompt_injection", "rag_integrity"], "url": "https://arxiv.org/abs/2302.12173"},
    {"id": "carlini-2024", "name": "Stealing Part of a Production Language Model", "date": "2024-03-11", "org": "Carlini et al.", "product": "Production LLM APIs",
     "summary": "Ordinary API queries recovered a model's embedding projection layer; under USD 20 for the smaller models studied.",
     "defenses": ["model_extraction"], "url": "https://arxiv.org/abs/2403.06634"},
    {"id": "anthropic-distillation", "name": "Detecting and preventing distillation attacks", "date": "2026-02-23", "org": "Anthropic", "product": "Claude API",
     "summary": "Reported large distillation campaigns run through networks of fraudulent accounts; per-account limits alone do not see them.",
     "defenses": ["model_extraction"], "url": "https://www.anthropic.com/news/detecting-and-preventing-distillation-attacks"},
    {"id": "lethal-trifecta", "name": "The lethal trifecta", "date": "2025-06-16", "org": "Simon Willison", "product": "Agent design",
     "summary": "Private data + untrusted content + external communication in one agent is the exfiltration precondition; remove one leg.",
     "defenses": ["egress"], "url": "https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/"},
]


def catalog() -> dict:
    return {"defenses": DEFENSES, "incidents": INCIDENTS, "evidence_type": "DOCUMENTED_SOURCES",
            "note": "Incident summaries are high-level and cited; demos use inert fixtures and public benchmarks."}


# ------------------------------------------------------------------------------------------------- lab
EGRESS_POLICY = EgressPolicy(allowed_domains=("acme.example",))
DEMO_SECRET = "CANARY-DEMO-7Q2X9"

EGRESS_CASES = [
    # (name, kind, payload, taint) -- inert fixtures of the documented channels, not working attacks
    ("internal_link_answer", "output", "Onboarding steps are on [the wiki](https://wiki.acme.example/onboarding).", {}),
    ("external_image_in_answer", "output", "Summary done. ![status](https://img.external.example/s.png)", {}),
    ("reference_style_image", "output", "Summary done. ![s][r]\n\n[r]: https://img.external.example/s.png", {}),
    ("protected_value_in_link", "output", f"[details](https://wiki.acme.example/x?k={DEMO_SECRET})", {}),
    ("email_internal_recipient", "tool", ("send_email", {"to": "dana@acme.example", "subject": "Agenda", "body": "See you at 10."}), {}),
    ("email_external_recipient", "tool", ("send_email", {"to": "someone@external.example", "subject": "Agenda", "body": "Notes"}), {}),
    ("hidden_bcc_external", "tool", ("send_email", {"to": "dana@acme.example", "bcc": "copy@external.example", "subject": "Invoice", "body": "Attached"}), {}),
    ("secret_in_tool_argument", "tool", ("add", {"a": 2, "b": 5, "note": DEMO_SECRET}), {"protected_values": (DEMO_SECRET,)}),
    ("private_data_to_public_pr", "tool", ("create_pull_request", {"repo": "public-site", "title": "Docs", "body": "update"}), {"private_data_read": True}),
    ("lethal_trifecta_send", "tool", ("send_email", {"to": "dana@acme.example", "subject": "Summary", "body": "ok"}),
     {"private_data_read": True, "untrusted_content_seen": True}),
]


def egress_case(kind: str, payload, taint: dict) -> dict:
    t = SessionTaint(**taint)
    if kind == "output":
        r = sanitize_output(payload, EGRESS_POLICY, t.protected_values or (DEMO_SECRET,))
        verdict = "withhold" if r["withhold"] else "sanitized" if r["modified"] else "pass"
        return {"verdict": verdict, "released_text": "" if r["withhold"] else r["text"], "findings": r["findings"]}
    tool, args = payload
    r = check_tool_call(tool, args, EGRESS_POLICY, t)
    return {"verdict": r["decision"], "reasons": r["reasons"], "destinations": r.get("destinations", [])}


def run_lab() -> dict:
    """Run every defense on its fixtures; unprotected vs protected for the shared scenario suite."""
    scen = []
    for case in builtin_scenarios():
        u, p = run_scenario(case, False), run_scenario(case, True)
        scen.append({"scenario": case.name, "category": case.category, "attacked": case.attacked,
                     "question": case.question,
                     "unprotected": {"released": u["response_released"], "unsafe_tool_would_run": u["unauthorized_action_would_execute"],
                                     "context_docs": u["context_doc_ids"], "output": u["output"], "tool": u["policy"]["tool"]},
                     "protected": {"released": p["response_released"], "unsafe_tool_would_run": p["unauthorized_action_would_execute"],
                                   "context_docs": p["context_doc_ids"], "tool_decision": p["policy"]["reason"],
                                   "rejected_docs": [d["id"] for d in p["documents"] if not d["allowed_to_context"]],
                                   "markers": p["prompt_markers"]}})
    egress = [{"case": n, "kind": k, **egress_case(k, pl, t)} for n, k, pl, t in EGRESS_CASES]
    mcp = synthetic_mcp_suite()
    extraction = synthetic_extraction_suite()
    campaign = synthetic_campaign_suite()
    return {
        "evidence_type": EVIDENCE, "engine": "deterministic fixtures; no LLM, no tool execution",
        "scenario_suite": {"cases": scen, "n": len(scen),
                           "unprotected_unsafe_actions": sum(c["unprotected"]["unsafe_tool_would_run"] for c in scen),
                           "protected_unsafe_actions": sum(c["protected"]["unsafe_tool_would_run"] for c in scen),
                           "note": "Unprotected output comes from a labeled non-LLM fixture that follows injected text, "
                                   "to show what the controls change. It is not a model measurement."},
        "egress": {"cases": egress, "n": len(egress)},
        "mcp_supply_chain": {"cases": [{"case": r["scenario"], "allowed": r["allowed"], "issues": r.get("issues", [])}
                                       for r in mcp["results"]], "blocked": mcp["blocked"], "allowed": mcp["allowed"],
                             "engine": mcp["engine"]},
        "model_extraction": {"per_account": [{"case": r["scenario"], "decision": r["decision"], "issues": r["issues"]}
                                             for r in extraction["results"]],
                             "campaign": campaign},
    }


def try_input(kind: str, body: dict) -> dict:
    """Interactive, bounded checks for the web UI. Never executes a tool; never calls a model."""
    if kind == "prompt_injection":
        text = str(body.get("text", ""))[:4000]
        markers = scan_injection(text)
        return {"verdict": "deny" if markers else "pass", "markers": markers, "evidence_type": EVIDENCE,
                "note": "Pattern screening only. The Attention Tracker signal needs a GPU model run."}
    if kind == "egress_output":
        r = egress_case("output", str(body.get("text", ""))[:8000], {})
        return {**r, "evidence_type": EVIDENCE}
    if kind == "egress_tool":
        tool = str(body.get("tool", ""))[:64]
        args = body.get("args") if isinstance(body.get("args"), dict) else {}
        args = {str(k)[:40]: str(v)[:2000] for k, v in list(args.items())[:12]}
        taint = {"private_data_read": bool(body.get("private_data_read")),
                 "untrusted_content_seen": bool(body.get("untrusted_content_seen")),
                 "protected_values": (DEMO_SECRET,)}
        return {**egress_case("tool", (tool, args), taint), "evidence_type": EVIDENCE}
    raise ValueError("unknown check")
