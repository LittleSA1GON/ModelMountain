# Model Mountain — observed evaluation limits

The current regex preflight was run on 20 hand-authored diagnostic cases on
2026-10-23. Evidence is CPU_HEURISTIC_AUDIT_NOT_MODEL_ROBUSTNESS.
It flagged 5/10 malicious-intent examples and incorrectly flagged
5/10 benign examples. These are exact observations on this tiny diagnostic sample,
not estimates for real user traffic and not an LLM attack-success benchmark.

Missed cases: attack_semantic, attack_encoded, attack_homoglyph, attack_multilingual, attack_answer_override.
False positives: benign_negation, benign_quote, benign_security_question, benign_test_description, benign_privacy.

This illustrates semantic/multilingual/obfuscated evasions and benign quoted/negated
security text. Regex screening alone cannot establish model security. Exact source
quotes can remain factually wrong when approved sources are wrong; lexical citation
matching cannot establish semantic truth. Model extraction protection is heuristic
admission control, not a universal extraction detector. Distributed quotas and enterprise
authentication need separate real integration checks.

The production scorer separates incorrect answers, false refusals, appropriate
abstention, compromised outcomes and unknown/backend failures. It reports observed and
pessimistic ASR bounds, sample sizes and Wilson intervals, with an explicit warning
that correlated task variants need grouped uncertainty analysis. Model interventions
require held-out generation, independently adjudicated labels, negative controls,
per-model/layer/strength ablations and benign-utility checks. Classifier separation
alone does not establish causal improvement or subjective model emotion.

Artifacts: model_mountain_results/preparation/preflight-diagnostic-cases.json and
preflight-diagnostic-report.json (including source hash). Reproduce using the
production audit_preflight function in model_mountain.benchmark_metrics.

Broader evaluation targets, not claimed executed results: [BIPIA](https://github.com/microsoft/BIPIA)
for indirect prompt injection; [AgentDojo](https://github.com/ethz-spylab/agentdojo) for
tool-using agent tasks with untrusted inputs; [RAGTruth](https://arxiv.org/abs/2401.00396)
for annotated hallucination examples. Any import must pin revision, license, provenance
and task-group splits. Adapt tool environments to inert sinks. Public published scores
are not Model Mountain scores. No aggregate model-security or hallucination-reduction
claim is supported until an actual compatible model trial and independent review finish.
