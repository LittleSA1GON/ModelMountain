"""Protection steering (injection shield): ingest binding and Steering catalog/preview, on a metadata fixture.

The fixture checks plumbing only; it is never written to api/experiments.json and makes no model claim.
"""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QWEN = "Qwen/Qwen2.5-1.5B-Instruct"


def _ingest_module():
    spec = importlib.util.spec_from_file_location("mm_ingest", ROOT / "scripts/ingest_kaggle_results.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rate(k, n):
    return {"k": k, "n": n, "rate": k / n, "ci95": [0.0, 1.0]}


class ShieldIngestTests(unittest.TestCase):
    def _fixture(self, d: Path, *, tamper=False):
        ing = _ingest_module()
        rev = ing.pinned_spec(QWEN).revision
        vdir = d / "vectors" / QWEN.replace("/", "__")
        vdir.mkdir(parents=True)
        f = vdir / "injection_shield__L10.pt"
        f.write_bytes(b"fixture-bytes")
        sha = hashlib.sha256(f.read_bytes()).hexdigest()
        (d / "summary.json").write_text(json.dumps({"project_id": "16f864bfa1303fc9", "kind": "shield",
                                                    "phases": [{"phase": "shield", "model": QWEN, "rc": 0}]}))
        doc = {"project_id": "16f864bfa1303fc9", "model_id": QWEN, "revision": rev, "evidence_type": "REAL_IBM_MIA",
               "benchmark": "Tensor Trust", "n_validation": 80, "n_test": 142,
               "artifact": {"concept": "injection_shield", "model_id": QWEN, "revision": rev, "block": 10, "hidden_size": 1536,
                            "method": "negated_hijack_compliance_mean_difference", "sha256": "0" * 64 if tamper else sha,
                            "path": "/kaggle/working/mm_results/vectors/x/injection_shield__L10.pt",
                            "evidence_type": "REAL_IBM_MIA", "mean_token_norm": 40.0, "direction_source": "fixture"},
               "validation": {"bare_attack_success": 0.6, "bare_access_granted": 0.6, "chosen_strength": 0.2,
                              "utility_constraint_met": True,
                              "sweep": [{"strength": 0.1, "attack_success": 0.5, "access_granted": 0.6},
                                        {"strength": 0.2, "attack_success": 0.4, "access_granted": 0.55}]},
               "test": {"bare": {"attack_success": _rate(75, 142), "access_code_utility": _rate(81, 142)},
                        "shield": {"attack_success": _rate(60, 142), "access_code_utility": _rate(78, 142), "strength": 0.2,
                                   "paired_vs_bare": {"mean_diff": -0.1, "ci95": [-0.2, -0.01]}, "examples": []}},
               "truthfulqa_mc1": {"bare": {"accuracy": _rate(50, 120)}, "shield": {"accuracy": _rate(48, 120)}}}
        (d / f"shield__{QWEN.replace('/', '__')}.json").write_text(json.dumps(doc))
        return ing

    def test_shield_binds_to_verified_vector_and_feeds_protection_preset(self):
        from model_mountain.steering_lab import build_profile, catalog
        with tempfile.TemporaryDirectory() as d:
            ing = self._fixture(Path(d))
            ing.SHIELD_FROM[:] = [Path(d)]
            sh = ing._shield(QWEN)
            self.assertEqual(sh["artifact"]["block"], 10)
            exp = {"schema": "mm-experiments-v1", "project_id": "16f864bfa1303fc9",
                   "models": [{"model_id": QWEN, "revision": ing.pinned_spec(QWEN).revision, "status": "measured", "shield": sh}]}
            row = next(m for m in catalog(exp)["models"] if m["model_id"] == QWEN)
            self.assertEqual(row["mvp_preset"]["concept"], "injection_shield")
            self.assertEqual(row["mvp_preset"]["strength"], 0.2)
            self.assertEqual(row["shield"]["status"], "measured")
            r = build_profile({"model_id": QWEN, **{k: row["mvp_preset"][k] for k in ("concept", "strength", "block", "phase", "positions")},
                               "opt_in": True}, exp)
            self.assertEqual(r["status"], "bound_to_real_vector")
            self.assertAlmostEqual(r["ibm_steer_payload"]["coefficient"], 8.0)
            self.assertEqual(r["preview"]["kind"], "protection")
            self.assertEqual(r["preview"]["status"], "measured")
            other = build_profile({"model_id": QWEN, "concept": "injection_shield", "strength": 0.1, "opt_in": True}, exp)
            self.assertEqual(other["preview"]["status"], "validation_only")

    def test_tampered_shield_vector_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            ing = self._fixture(Path(d), tamper=True)
            ing.SHIELD_FROM[:] = [Path(d)]
            with self.assertRaises(ValueError):
                ing._shield(QWEN)

    def test_pending_shield_has_preset_but_no_payload(self):
        from model_mountain.steering_lab import build_profile, catalog
        row = next(m for m in catalog(None)["models"] if m["model_id"] == QWEN)
        self.assertEqual(row["shield"]["status"], "gpu_run_pending")
        r = build_profile({"model_id": QWEN, "concept": "injection_shield", "strength": 0.1, "opt_in": True}, None)
        self.assertEqual(r["status"], "vector_not_captured_yet")
        self.assertIsNone(r["ibm_steer_payload"])
        self.assertEqual(r["profile"]["block"], 10)


if __name__ == "__main__":
    unittest.main()
