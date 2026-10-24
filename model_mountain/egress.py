"""Defense 3: data-exfiltration (egress) guard for agent tool calls and rendered model output.

Documented exfiltration channels this layer targets (see ``model_mountain.defenses.INCIDENTS``):

* rendered Markdown images / links whose URL carries private data (EchoLeak CVE-2025-32711,
  PromptArmor's Slack AI report, Legit Security's CamoLeak) -> output sanitizer;
* tool calls that send private data to an attacker-reachable sink (Invariant Labs' GitHub MCP report,
  General Analysis' Supabase MCP report, the postmark-mcp BCC backdoor) -> tool-call egress policy;
* the "lethal trifecta" (Willison, 2025): private data + untrusted content + an external channel in one
  session -> require human approval before any external send.

Deterministic, model-independent and deny-by-default. It never executes a tool. It does not prove that
an output is safe; it removes the documented channels and refuses unapproved external destinations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import re
from collections import Counter
from urllib.parse import unquote, urlsplit

# --------------------------------------------------------------------------------------- URL extraction
_INLINE_IMAGE = re.compile(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
_INLINE_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
_REF_USE = re.compile(r"(!?)\[[^\]]*\]\[([^\]]*)\]")
_REF_DEF = re.compile(r"^[ \t]{0,3}\[([^\]]+)\]:[ \t]*<?(\S+?)>?(?:[ \t]+.*)?$", re.M)
_HTML_SRC = re.compile(r"<(?:img|image|iframe|script|link|a)\b[^>]*?\b(?:src|href)\s*=\s*[\"']?([^\"'\s>]+)", re.I)
_BARE = re.compile(r"\bhttps?://[^\s<>\"')\]]+", re.I)

DEFAULT_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:sk-|ghp_|github_pat_|xox[baprs]-)[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bCANARY-[A-Z0-9-]{6,}\b"),          # demo secrets in this repo
)

EXTERNAL_SINKS = {
    # tool name -> argument fields that carry a destination
    "send_email": ("to", "cc", "bcc"),
    "http_get": ("url",),
    "http_post": ("url",),
    "fetch_url": ("url",),
    "post_message": ("channel",),
    "create_pull_request": ("repo",),
    "create_issue": ("repo",),
    "post_ticket_message": ("ticket_id",),
    "upload_file": ("destination",),
}


def _host(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""


def domain_allowed(host_or_email: str, allowed: tuple[str, ...]) -> bool:
    """Exact-or-subdomain match against an allowlist of registrable domains (no wildcards)."""
    host = host_or_email.split("@")[-1].strip().lower().rstrip(".")
    return bool(host) and any(host == d or host.endswith("." + d) for d in allowed)


def extract_urls(text: str) -> list[dict]:
    """All URLs a Markdown/HTML renderer could fetch or show, incl. reference-style definitions."""
    text = text or ""
    found = []
    defs = {m.group(1).strip().lower(): m.group(2) for m in _REF_DEF.finditer(text)}
    for m in _INLINE_IMAGE.finditer(text):
        found.append({"url": m.group(1), "kind": "image", "auto_fetch": True})
    for m in _INLINE_LINK.finditer(text):
        found.append({"url": m.group(1), "kind": "link", "auto_fetch": False})
    for m in _REF_USE.finditer(text):
        ref = (m.group(2) or "").strip().lower()
        if ref in defs:
            found.append({"url": defs[ref], "kind": "image" if m.group(1) else "link", "auto_fetch": bool(m.group(1)),
                          "reference_style": True})
    for ref, url in defs.items():
        if not any(f.get("reference_style") and f["url"] == url for f in found):
            found.append({"url": url, "kind": "reference_definition", "auto_fetch": False, "reference_style": True})
    for m in _HTML_SRC.finditer(text):
        found.append({"url": m.group(1), "kind": "html", "auto_fetch": True})
    seen = {f["url"] for f in found}
    for m in _BARE.finditer(text):
        if m.group(0) not in seen:
            found.append({"url": m.group(0), "kind": "bare", "auto_fetch": False})
    return found


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    c = Counter(s)
    return -sum(n / len(s) * math.log2(n / len(s)) for n in c.values())


def url_carries_data(url: str, protected_values: tuple[str, ...] = (), *, patterns=DEFAULT_SECRET_PATTERNS) -> list[str]:
    """Reasons a URL looks like an exfiltration carrier (protected value, secret pattern, long opaque token)."""
    reasons = []
    decoded = unquote(url or "")
    for v in protected_values:
        if len(v) >= 6 and v.lower() in decoded.lower():
            reasons.append("protected_value_in_url")
            break
    if any(p.search(decoded) for p in patterns):
        reasons.append("secret_pattern_in_url")
    try:
        parts = urlsplit(decoded)
        chunks = re.split(r"[/?&=#;,]", (parts.path or "") + "?" + (parts.query or ""))
    except ValueError:
        chunks = []
    if any(len(c) >= 24 and _entropy(c) >= 3.5 for c in chunks):
        reasons.append("high_entropy_token_in_url")
    return reasons


@dataclass(frozen=True)
class EgressPolicy:
    allowed_domains: tuple[str, ...] = ("acme.example",)
    render_external_images: bool = False      # EchoLeak/CamoLeak mitigation: never auto-fetch external images
    approval_required_for_external_send: bool = True
    patterns: tuple = DEFAULT_SECRET_PATTERNS


@dataclass
class SessionTaint:
    """What this agent session has touched. Set by trusted application code, never by the model."""
    private_data_read: bool = False
    untrusted_content_seen: bool = False
    protected_values: tuple[str, ...] = ()
    sources: list = field(default_factory=list)

    def lethal_trifecta(self) -> bool:
        return self.private_data_read and self.untrusted_content_seen


def sanitize_output(text: str, policy: EgressPolicy, protected_values: tuple[str, ...] = ()) -> dict:
    """Neutralize Markdown/HTML channels that could leak data when the answer is rendered.

    External images are always removed (auto-fetch = zero-click). Links to non-allowlisted domains are
    shown as inert text. Any URL carrying protected/secret-looking data is removed regardless of domain.
    """
    findings, out = [], text or ""
    urls = extract_urls(out)
    for f in urls:
        host = _host(f["url"])
        allowed = domain_allowed(host, policy.allowed_domains) if host else False
        carrier = url_carries_data(f["url"], protected_values, patterns=policy.patterns)
        bad = bool(carrier) or (f["auto_fetch"] and not (allowed or policy.render_external_images)) or \
            (f["kind"] in ("link", "bare", "reference_definition", "html") and host and not allowed)
        if bad:
            findings.append({"url_host": host or "(relative)", "kind": f["kind"], "reasons": carrier or
                             (["external_image_auto_fetch"] if f["auto_fetch"] else ["non_allowlisted_link"])})
            out = out.replace(f["url"], "[link removed by Model Mountain egress guard]")
    # Inline images whose URL was removed should not leave a broken image tag behind.
    out = re.sub(r"!\[([^\]]*)\]\(\[link removed by Model Mountain egress guard\]\)", r"[image removed: \1]", out)
    leaked = [p.pattern for p in policy.patterns if p.search(out)]
    leaked += ["protected_value_in_text" for v in protected_values if len(v) >= 6 and v in out]
    if leaked:
        findings.append({"url_host": None, "kind": "text", "reasons": sorted(set(
            "secret_pattern_in_text" if r != "protected_value_in_text" else r for r in leaked))})
    return {"text": out, "findings": findings, "modified": out != (text or ""),
            "withhold": any("text" == f["kind"] for f in findings)}


def check_tool_call(tool: str, args: dict, policy: EgressPolicy, taint: SessionTaint) -> dict:
    """Egress decision for one proposed tool call. Authorization (who may call it) is a separate layer."""
    if not isinstance(args, dict):
        return {"allowed": False, "decision": "deny", "reasons": ["invalid_tool_arguments"]}
    reasons, destinations = [], []
    sink_fields = EXTERNAL_SINKS.get(tool)
    flat = " ".join(str(v) for v in args.values())
    # 1. secret / protected value in ANY argument of ANY tool (incl. hidden 'sidenote'-style params)
    if any(p.search(flat) for p in policy.patterns):
        reasons.append("secret_pattern_in_tool_arguments")
    if any(len(v) >= 6 and v in flat for v in taint.protected_values):
        reasons.append("protected_value_in_tool_arguments")
    for f in extract_urls(flat):
        carrier = url_carries_data(f["url"], taint.protected_values, patterns=policy.patterns)
        if carrier:
            reasons.extend(r + "_in_tool_arguments" for r in carrier)
    if sink_fields is None:
        return {"allowed": not reasons, "decision": "deny" if reasons else "allow", "reasons": sorted(set(reasons)),
                "external_sink": False, "destinations": []}
    # 2. destination allowlist for external sinks (email recipients incl. cc/bcc, URL hosts, repos/channels)
    if not any(args.get(f) for f in sink_fields):
        reasons.append("missing_destination")             # a sink call without a destination is never allowed
    for fld in sink_fields:
        val = args.get(fld)
        if not val:
            continue
        if fld in ("url", "destination"):
            try:
                u = urlsplit(str(val))
            except ValueError:
                u = None
            if u is None or u.scheme not in ("http", "https") or u.username or u.password or not u.hostname:
                reasons.append(f"unsafe_url_form:{fld}")   # only plain http(s), no embedded credentials
        for item in (val if isinstance(val, list) else re.split(r"[,;\s]+", str(val))):
            if not item:
                continue
            target = _host(item) if "://" in item else item
            destinations.append({"field": fld, "target": target})
            if fld in ("to", "cc", "bcc", "url", "destination"):
                if not domain_allowed(target, policy.allowed_domains):
                    reasons.append(f"non_allowlisted_destination:{fld}")
    if tool in ("create_pull_request", "create_issue", "post_ticket_message", "post_message") and taint.private_data_read:
        reasons.append("private_data_to_shared_or_public_sink")
    # 3. lethal trifecta breaker: never auto-send externally once private data AND untrusted content met
    needs_approval = policy.approval_required_for_external_send and taint.lethal_trifecta()
    decision = "deny" if reasons else ("require_human_approval" if needs_approval else "allow")
    return {"allowed": decision == "allow", "decision": decision, "reasons": sorted(set(reasons)) +
            (["lethal_trifecta_private_plus_untrusted_plus_external"] if needs_approval and not reasons else []),
            "external_sink": True, "destinations": destinations}
