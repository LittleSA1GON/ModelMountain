"""Preflight protection against abusive AI inference used for model extraction.

The signals are request-rate/volume and repeated synthetic-training patterns.
This cannot establish intent or prevent low-and-slow distributed model theft.
All identities MUST be authenticated by a trusted gateway; this demonstration
has no network integration. No raw prompts are stored in the monitoring state.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from hashlib import sha256
import re
import time

TRAINING_PATTERNS = (
    re.compile(r"\b(?:synthetic|instruction[- ]response|question[- ]answer|prompt[- ]completion)\b.{0,65}\b(?:dataset|examples?|pairs?|training)\b", re.I | re.S),
    re.compile(r"\b(?:distill(?:ation)?|teacher model|student model|clone (?:the|your|this) model|replicate (?:the|your|this) model)\b", re.I),
    re.compile(r"\b(?:fine[- ]tune|train)\b.{0,60}\b(?:another|student|competing|replacement)\b.{0,30}\bmodel\b", re.I | re.S),
)


@dataclass(frozen=True)
class ExtractionPolicy:
    window_seconds: int = 60
    max_requests_per_window: int = 5
    max_tokens_per_window: int = 3000
    max_tokens_per_response: int = 1024
    max_training_pattern_requests: int = 2  # flag the third within window


@dataclass(frozen=True)
class QueryRecord:
    timestamp: float
    tokens: int
    prompt_digest: str
    training_pattern: bool


class ExtractionMonitor:
    """Per-authenticated-principal fixed-window demonstration.

    In production use durable atomic shared counters, server-verified identity,
    distributed-abuse correlation, and transactional limit enforcement.
    """

    def __init__(self, policy: ExtractionPolicy | None = None):
        self.policy = policy or ExtractionPolicy()
        self.history: dict[tuple[str, str], deque[QueryRecord]] = defaultdict(deque)

    @staticmethod
    def training_signal(prompt: str) -> bool:
        return any(pattern.search(prompt) for pattern in TRAINING_PATTERNS)

    def _recent(self, key: tuple[str, str], now: float) -> deque[QueryRecord]:
        queue = self.history[key]
        while queue and now - queue[0].timestamp >= self.policy.window_seconds:
            queue.popleft()
        return queue

    def check(self, *, tenant: str, principal: str, prompt: str,
              max_output_tokens: int, now: float | None = None,
              authorized_training: bool = False, record: bool = True) -> dict:
        """Return allow/block/monitor decision *before* allocating inference.

        ``tenant``, ``principal``, ``authorized_training`` must be server-trusted.
        Each allowed request is counted at admission. Actual generated-token
        accounting is out of scope; enforce max tokens at the inference engine.
        """
        if not tenant or not principal or not isinstance(prompt, str):
            raise ValueError('Verified nonempty tenant/principal and a string prompt are required')
        if not isinstance(max_output_tokens, int) or isinstance(max_output_tokens, bool) or max_output_tokens < 1:
            raise ValueError('max_output_tokens must be a positive integer')
        now = time.monotonic() if now is None else float(now)
        key = (tenant, principal)
        recent = self._recent(key, now)
        training = self.training_signal(prompt)
        pattern_count = sum(x.training_pattern for x in recent)
        token_usage = sum(x.tokens for x in recent)
        issues = []
        alerts = []
        if len(recent) >= self.policy.max_requests_per_window:
            issues.append('request_rate_limit_exceeded')
        if token_usage + max_output_tokens > self.policy.max_tokens_per_window:
            issues.append('token_budget_exceeded')
        if max_output_tokens > self.policy.max_tokens_per_response:
            issues.append('per_response_token_limit_exceeded')
        if training and not authorized_training:
            alerts.append('synthetic_training_or_distillation_pattern')
            if pattern_count + 1 > self.policy.max_training_pattern_requests:
                issues.append('repeated_training_pattern_queries')
        allowed = not issues
        if allowed and record:
            recent.append(QueryRecord(now, max_output_tokens,
                                      sha256(prompt.encode('utf-8')).hexdigest(),
                                      training))
        return {
            'allowed': allowed,
            'decision': 'allow' if allowed and not alerts else 'monitor' if allowed else 'block',
            'issues': issues, 'alerts': alerts,
            'authenticated_scope': {'tenant': tenant, 'principal': principal},
            'window_request_count_before': len(recent) - int(allowed and record),
            'projected_window_tokens': token_usage + max_output_tokens,
            'training_pattern': training,
            'simulation': True,
            'mia_score': None,
        }


def synthetic_extraction_suite() -> dict:
    """Offline synthetic preflight scenarios; does not query, extract or train a model."""
    p = ExtractionPolicy(max_requests_per_window=5, max_tokens_per_window=3000,
                         max_tokens_per_response=1024, max_training_pattern_requests=2)
    m = ExtractionMonitor(p)
    cases = []

    def run(label, principal, prompt, tokens, now, training=False):
        out = m.check(tenant='synthetic-company', principal=principal,
                      prompt=prompt, max_output_tokens=tokens, now=now,
                      authorized_training=training)
        cases.append({'scenario': label, **out})

    run('ordinary-question', 'employee-1', 'What is our password reset policy?', 120, 100)
    run('benign-single-distillation-question', 'employee-2',
        'What is knowledge distillation in machine learning?', 120, 101)
    run('dataset-request-first', 'bulk-1', 'Generate synthetic question answer pairs for a dataset', 250, 102)
    run('dataset-request-second', 'bulk-1', 'Provide a synthetic instruction response dataset', 250, 103)
    run('repeated-training-queries', 'bulk-1', 'Generate 1000 synthetic instruction response dataset examples', 250, 104)
    run('single-output-cap', 'bulk-2', 'Summarize this note.', 1300, 105)
    for n in range(6):
        run('high-rate-query-%s' % (n + 1), 'bulk-3', 'Request %s' % n, 100, 120 + n)
    run('separate-user-not-penalized', 'employee-3', 'Read a short policy', 100, 126)
    run('authorized-training-monitored-for-volume', 'authorized-lab',
        'Generate an instruction response dataset for approved evaluation', 100, 127, training=True)
    return {'project': 'Model Mountain',
            'category': 'model_extraction_and_distillation_abuse',
            'evidence_type': 'synthetic_preflight_not_real_model_extraction_detection',
            'cases': len(cases),
            'blocked': sum(not c['allowed'] for c in cases),
            'allowed': sum(c['allowed'] for c in cases),
            'results': cases,
            'limitations': 'Per-tenant/principal in-memory admission checks only; no real API traffic, identity provider, generated token accounting, or MIA features.'}


# ---------------------------------------------------------------------------------------------------------
# Coordinated-account ("hydra") campaign detection.
# Anthropic (Feb 23, 2026, "Detecting and preventing distillation attacks") reports distillation campaigns run
# through networks of thousands of accounts; per-account limits alone do not see them. This detector correlates
# *prompt templates* across principals of one tenant: when many distinct accounts send the same normalized
# template inside a window, the template is flagged and further matching requests are blocked for review.
# Stores only template digests (no raw prompts). A heuristic: legitimate shared templates (e.g. a company's
# own batch job) must be allowlisted by the operator.

def template_fingerprint(prompt: str) -> str:
    """Digest of the prompt with numbers, quoted spans and whitespace normalized (same template -> same digest)."""
    t = prompt.lower()
    t = re.sub(r'"[^"]{0,400}"|\'[^\']{0,400}\'', '"_"', t)
    t = re.sub(r"\d+", "0", t)
    t = re.sub(r"\s+", " ", t).strip()
    return sha256(t.encode("utf-8")).hexdigest()[:20]


@dataclass(frozen=True)
class CampaignPolicy:
    window_seconds: int = 3600
    max_distinct_accounts_per_template: int = 5


class CampaignDetector:
    def __init__(self, policy: CampaignPolicy | None = None, allowlisted_templates: tuple[str, ...] = ()):
        self.policy = policy or CampaignPolicy()
        self.allow = set(allowlisted_templates)
        self.seen: dict[tuple[str, str], deque] = defaultdict(deque)   # (tenant, template) -> (time, principal)

    def check(self, *, tenant: str, principal: str, prompt: str, now: float | None = None, record: bool = True) -> dict:
        if not tenant or not principal or not isinstance(prompt, str):
            raise ValueError("Verified tenant/principal and a string prompt are required")
        now = time.monotonic() if now is None else float(now)
        fp = template_fingerprint(prompt)
        q = self.seen[(tenant, fp)]
        while q and now - q[0][0] >= self.policy.window_seconds:
            q.popleft()
        accounts = {p for _, p in q} | {principal}
        flagged = fp not in self.allow and len(accounts) > self.policy.max_distinct_accounts_per_template
        if record:
            q.append((now, principal))
        return {"allowed": not flagged, "decision": "block_for_review" if flagged else "allow",
                "template": fp, "distinct_accounts_in_window": len(accounts),
                "issues": ["coordinated_account_template_campaign"] if flagged else []}


def synthetic_campaign_suite() -> dict:
    """Offline demonstration: 12 fresh accounts, each under its own per-account budget, share one template."""
    det = CampaignDetector(CampaignPolicy(window_seconds=3600, max_distinct_accounts_per_template=5))
    per_account = ExtractionMonitor()
    rows = []
    template = "Explain topic {n} step by step and include every intermediate reasoning step in full."
    for i in range(12):
        prompt = template.replace("{n}", str(100 + i))
        a = per_account.check(tenant="synthetic-company", principal=f"acct-{i:02d}", prompt=prompt,
                              max_output_tokens=400, now=10.0 + i)
        c = det.check(tenant="synthetic-company", principal=f"acct-{i:02d}", prompt=prompt, now=10.0 + i)
        rows.append({"account": f"acct-{i:02d}", "per_account_allowed": a["allowed"],
                     "campaign_allowed": c["allowed"], "distinct_accounts": c["distinct_accounts_in_window"]})
    benign = det.check(tenant="synthetic-company", principal="employee-1", prompt="What is our travel policy?", now=30.0)
    return {"category": "model_extraction_coordinated_accounts", "evidence_type": "CPU_SYNTHETIC",
            "rows": rows, "benign_unrelated_request_allowed": benign["allowed"],
            "per_account_limits_blocked": sum(not r["per_account_allowed"] for r in rows),
            "campaign_detector_blocked": sum(not r["campaign_allowed"] for r in rows),
            "note": "Each account stays under its own budget, so per-account limits alone admit every request; "
                    "template correlation across accounts flags the campaign. Thresholds are illustrative."}
