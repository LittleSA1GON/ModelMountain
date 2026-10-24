"""Calibrated IBM MIA risk scores. Never infer attack-risk direction by default.

The scorer itself is supplied by a genuine IBM MIA runtime. A threshold trained on
labeled real captures is *not* a security guarantee and should be evaluated on a
separate held-out attack set, plus benign tasks, before release.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class MiaRiskPolicy:
    model_id: str
    threshold: float
    risky_when: str
    analyzer: str = 'attn_tracker'
    provenance: str = 'real_IBM_MIA_scores_calibrated_on_labeled_examples'
    benign_examples: int = 0
    attack_examples: int = 0

    def __post_init__(self):
        if self.risky_when not in ('higher', 'lower') or self.analyzer != 'attn_tracker':
            raise ValueError('Unsupported MIA score direction or analyzer')
        if not self.model_id or not math.isfinite(self.threshold):
            raise ValueError('MIA model and finite threshold required')

    def flags(self, score: float, model_id: str) -> bool:
        if model_id != self.model_id:
            raise ValueError('Model mismatch: never transfer MIA thresholds across models')
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not math.isfinite(score):
            raise ValueError('Missing or nonfinite genuine MIA score')
        return score >= self.threshold if self.risky_when == 'higher' else score <= self.threshold

    def save(self, path: str | Path):
        Path(path).write_text(json.dumps(asdict(self), indent=2), encoding='utf-8')

    @classmethod
    def load(cls, path: str | Path):
        raw = json.loads(Path(path).read_text(encoding='utf-8'))
        return cls(**raw)


def calibrate_mia_scores(*, model_id: str, benign: list[float], attacks: list[float],
                         max_false_positive_rate: float = 0.25) -> tuple[MiaRiskPolicy, dict]:
    """Choose a reproducible threshold from labeled REAL MIA scores.

    Optimize recall subject to a benign FPR ceiling, and break ties using lower
    FPR then accuracy. Calibration examples are training data, NOT performance
    evidence. For a real system use many examples and an independent test set.
    """
    if len(benign) < 2 or len(attacks) < 2:
        raise ValueError('At least two real scores of each class required for a demo calibration')
    vals = [*benign, *attacks]
    if not all(isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v) for v in vals):
        raise ValueError('Only finite numeric scores are allowed')
    if not 0 <= max_false_positive_rate <= 1:
        raise ValueError('Invalid max_false_positive_rate')
    unique = sorted(set(vals))
    if len(unique) < 2:
        raise ValueError('No score separation: cannot calibrate useful MIA defense')
    spread = max(1.0, unique[-1] - unique[0])
    thresholds = [unique[0] - spread] + [(a+b)/2 for a, b in zip(unique, unique[1:])] + [unique[-1] + spread]
    candidates = []
    for direction in ('higher', 'lower'):
        for threshold in thresholds:
            attack_flags = [s >= threshold if direction == 'higher' else s <= threshold for s in attacks]
            benign_flags = [s >= threshold if direction == 'higher' else s <= threshold for s in benign]
            recall = sum(attack_flags) / len(attacks)
            fpr = sum(benign_flags) / len(benign)
            if fpr <= max_false_positive_rate and recall > 0:
                candidates.append((recall, -fpr, (sum(attack_flags)+len(benign)-sum(benign_flags)) / len(vals), direction, threshold))
    if not candidates:
        raise ValueError('No useful threshold meets the false-positive limit')
    recall, neg_fpr, accuracy, direction, threshold = max(candidates)
    policy = MiaRiskPolicy(model_id=model_id, threshold=float(threshold), risky_when=direction,
                           benign_examples=len(benign), attack_examples=len(attacks))
    return policy, {'calibration_recall': recall, 'calibration_false_positive_rate': -neg_fpr,
                    'calibration_accuracy': accuracy,
                    'note': 'Calibration-set metrics are NOT held-out benchmark results.'}
