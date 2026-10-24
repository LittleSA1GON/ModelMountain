"""Illustrative enterprise threat-model prioritization, NOT universal CVSS scores."""
from __future__ import annotations

RISKS = (
    {'priority': 1, 'risk': 'Unauthorized AI-agent actions', 'severity': 'Critical', 'why': 'Privileged tools can modify accounts, systems or records', 'protection': 'Independent tool authorization and approval', 'mia_role': 'Optional tool-risk analysis; not enforcement'},
    {'priority': 2, 'risk': 'Sensitive data exfiltration', 'severity': 'Critical', 'why': 'Credentials and private records can be disclosed', 'protection': 'Data access boundaries, DLP, egress limits', 'mia_role': 'Experimental leak-risk telemetry'},
    {'priority': 3, 'risk': 'Prompt injection', 'severity': 'Critical', 'why': 'Untrusted text can redirect tool-using models', 'protection': 'Trust boundaries, response gating, tested detectors', 'mia_role': 'Attention Tracker on supported models'},
    {'priority': 4, 'risk': 'MCP tool poisoning and malicious updates', 'severity': 'Critical', 'why': 'Previously approved tools can change behavior', 'protection': 'Signed manifests, tool pins, explicit approvals', 'mia_role': 'Optional inspection of resulting model behavior'},
    {'priority': 5, 'risk': 'RAG poisoning and unauthorized retrieval', 'severity': 'High', 'why': 'Retrieved text can mislead or manipulate answers', 'protection': 'Source integrity, provenance, tenant ACLs', 'mia_role': 'Attention monitoring; optional reranking research'},
    {'priority': 6, 'risk': 'MCP credential, OAuth and TLS failures', 'severity': 'High', 'why': 'Can enable impersonation and credential misuse', 'protection': 'Server authentication, token audiences, TLS checks', 'mia_role': 'None; protocol-layer security'},
    {'priority': 7, 'risk': 'Model extraction via distillation-style API use', 'severity': 'High', 'why': 'Systematic API queries may replicate proprietary behavior', 'protection': 'Per-account limits, token budgets, abuse telemetry', 'mia_role': 'Optional unvalidated internal telemetry'},
    {'priority': 8, 'risk': 'Agent memory poisoning', 'severity': 'High', 'why': 'Attacker text can persist across future sessions', 'protection': 'Trusted writes, provenance, review, expiry', 'mia_role': 'Possible investigation, not persistence control'},
    {'priority': 9, 'risk': 'Jailbreaks and guardrail bypass', 'severity': 'High', 'why': 'Can violate intended restrictions and safety policy', 'protection': 'Red teaming, external enforcement, policy checks', 'mia_role': 'Experimental steering and detection'},
    {'priority': 10, 'risk': 'Unsupported or fabricated enterprise answers', 'severity': 'Medium-High', 'why': 'May lead to incorrect consequential decisions', 'protection': 'Evidence verification and human review', 'mia_role': 'Experimental hallucination probes'},
)

RISK_ASSUMPTIONS = (
    'Illustrative severity for a company with internal RAG data and tool-using agents; '
    'not official OWASP/CVSS scoring, empirical prevalence, or a measured vulnerability assessment. '
    'Model extraction can be critical for proprietary API providers and lower for open-weight internal models.'
)
