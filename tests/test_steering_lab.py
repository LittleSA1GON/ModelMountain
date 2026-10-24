import json
import tempfile
import unittest
from pathlib import Path

from model_mountain.steering_lab import ProfileError, build_profile, catalog, load_experiments, preview

SHA = "ab" * 32
EXP = {"schema": "mm-experiments-v1", "project_id": "16f864bfa1303fc9", "models": [{
    "model_id": "Qwen/Qwen2.5-1.5B-Instruct", "revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306", "status": "measured",
    "emotions": {"selected_block": 18, "mean_token_norm_train": 50.0, "test_accuracy": 0.6, "chance": 0.1,
                 "vectors": [{"concept": "calm", "block": 18, "sha256": SHA, "hidden_size": 1536, "method": "m"}]},
    "steer": {"baseline": {"attack_success": {"rate": 0.4}}, "rows": [
        {"emotion": "calm", "strength": 0.1, "attack_success": {"rate": 0.3}},
        {"emotion": "calm", "strength": 0.2, "attack_success": {"rate": 0.25}}]}}]}


class SteeringLabTests(unittest.TestCase):
    def test_catalog_without_runs_marks_not_captured(self):
        rows = {m["model_id"]: m for m in catalog(None)["models"]}
        self.assertIn("ibm-granite/granite-3.1-2b-instruct", rows)
        self.assertEqual(rows["Qwen/Qwen2.5-1.5B-Instruct"]["evidence_type"], "NOT_CAPTURED")
        self.assertEqual(rows["Qwen/Qwen2.5-1.5B-Instruct"]["vectors"], [])

    def test_profile_binds_to_real_vector_and_scales_strength(self):
        r = build_profile({"model_id": "Qwen/Qwen2.5-1.5B-Instruct", "concept": "calm", "strength": 0.1, "opt_in": True}, EXP)
        self.assertEqual(r["status"], "bound_to_real_vector")
        self.assertAlmostEqual(r["ibm_steer_payload"]["coefficient"], 5.0)
        self.assertEqual(r["ibm_steer_payload"]["optimal_layer"], 18)
        self.assertEqual(r["profile"]["vector_sha256"], SHA)
        self.assertEqual(r["preview"]["status"], "measured")

    def test_unmeasured_strength_uses_nearest_and_says_so(self):
        p = preview(EXP, "Qwen/Qwen2.5-1.5B-Instruct", "calm", 0.17)
        self.assertEqual(p["status"], "nearest_measured")
        self.assertEqual(p["measured_strength"], 0.2)

    def test_off_layer_is_flagged_and_bounds_enforced(self):
        r = build_profile({"model_id": "Qwen/Qwen2.5-1.5B-Instruct", "concept": "calm", "strength": -0.1, "block": 5, "opt_in": True}, EXP)
        self.assertEqual(r["status"], "bound_off_layer_unvalidated")
        with self.assertRaises(ProfileError):
            build_profile({"model_id": "Qwen/Qwen2.5-1.5B-Instruct", "concept": "calm", "strength": 0.9, "opt_in": True}, EXP)
        with self.assertRaises(ProfileError):
            build_profile({"model_id": "Qwen/Qwen2.5-1.5B-Instruct", "concept": "calm", "strength": 0.1}, EXP)   # no opt-in
        with self.assertRaises(ProfileError):
            build_profile({"model_id": "evil/model", "concept": "calm", "strength": 0.1, "opt_in": True}, EXP)
        with self.assertRaises(ProfileError):
            build_profile({"model_id": "Qwen/Qwen2.5-1.5B-Instruct", "concept": "calm", "strength": 0.1, "block": 99, "opt_in": True}, EXP)

    def test_no_vector_yet_returns_pending_not_payload(self):
        r = build_profile({"model_id": "ibm-granite/granite-3.1-2b-instruct", "concept": "calm", "strength": 0.1, "block": 20, "opt_in": True}, None)
        self.assertEqual(r["status"], "vector_not_captured_yet")
        self.assertIsNone(r["ibm_steer_payload"])

    def test_load_experiments_rejects_foreign_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "e.json"
            p.write_text(json.dumps({**EXP, "project_id": "other"}))
            with self.assertRaises(ProfileError):
                load_experiments(p)


class DefenseLabTests(unittest.TestCase):
    def test_lab_protected_mode_blocks_all_unsafe_actions(self):
        from model_mountain.defenses import DEFENSES, INCIDENTS, run_lab
        self.assertEqual(len(DEFENSES), 5)
        ids = {d["id"] for d in DEFENSES}
        self.assertTrue(all(set(i["defenses"]) <= ids for i in INCIDENTS))
        r = run_lab()
        self.assertEqual(r["scenario_suite"]["protected_unsafe_actions"], 0)
        self.assertGreater(r["scenario_suite"]["unprotected_unsafe_actions"], 0)
        verdicts = {c["case"]: c["verdict"] for c in r["egress"]["cases"]}
        self.assertEqual(verdicts["internal_link_answer"], "pass")
        self.assertEqual(verdicts["email_internal_recipient"], "allow")
        self.assertEqual(verdicts["hidden_bcc_external"], "deny")
        self.assertEqual(verdicts["lethal_trifecta_send"], "require_human_approval")


if __name__ == "__main__":
    unittest.main()


class SteeringApplyTests(unittest.TestCase):
    def test_preview_flags_settings_that_differ_from_measured_reference(self):
        p = preview(EXP, "Qwen/Qwen2.5-1.5B-Instruct", "calm", 0.1, block=5, phase="decode", measured_block=18)
        self.assertEqual(p["status"], "reference_condition_differs")
        self.assertEqual(set(p["differs_in"]), {"block", "phase"})
        self.assertEqual(preview(EXP, "Qwen/Qwen2.5-1.5B-Instruct", "calm", 0.1, block=18, measured_block=18)["status"], "measured")

    def _run(self, d, sha, block=18):
        import json as _j
        man = {"project_id": "16f864bfa1303fc9", "evidence_type": "REAL_IBM_MIA", "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
               "revision": EXP['models'][0]['revision'], "selected": {"mean_token_norm_train": 50.0},
               "artifacts": [{"concept": "calm", "model_id": "Qwen/Qwen2.5-1.5B-Instruct", "revision": EXP['models'][0]['revision'], "block": block,
                              "hidden_size": 1536, "sha256": sha, "path": "/kaggle/working/mm_results/vectors/x/calm__L18.pt"}]}
        (Path(d) / "emotions__Qwen__Qwen2.5-1.5B-Instruct.json").write_text(_j.dumps(man))

    def test_resolver_binds_to_trusted_manifest_and_refuses_mismatches(self):
        import hashlib
        from model_mountain.steering_lab import resolve_vector
        with tempfile.TemporaryDirectory() as d:
            vdir = Path(d) / "vectors" / "x"; vdir.mkdir(parents=True)
            f = vdir / "calm__L18.pt"; f.write_bytes(b"not-a-real-tensor")
            sha = hashlib.sha256(f.read_bytes()).hexdigest()
            self._run(d, sha)
            good = {"model_id": "Qwen/Qwen2.5-1.5B-Instruct", "model_revision": EXP['models'][0]['revision'], "concept": "calm",
                    "vector_sha256": sha, "block": 18, "coefficient": 5.0, "method": "add_vector", "phase": "both",
                    "positions": "all_tokens"}
            cases = [dict(good, vector_sha256="0" * 64), dict(good, model_revision="s" * 40), dict(good, concept="angry"),
                     dict(good, block=3), dict(good, coefficient=float("nan")), dict(good, coefficient=1e6),
                     dict(good, model_revision=None), dict(good, model_id="ibm-granite/granite-3.1-2b-instruct")]
            for bad in cases:
                with self.assertRaises(ProfileError, msg=str({k: bad[k] for k in bad if bad[k] != good.get(k)})):
                    resolve_vector(bad, d)
            # a correct profile passes every provenance check and only stops at reading the (fake) tensor
            with self.assertRaises(ProfileError) as ctx:
                resolve_vector(good, d)
            self.assertIn("unreadable", str(ctx.exception))
            with self.assertRaises(ProfileError):
                resolve_vector(dict(good, block=999), d, allow_off_layer=True)
            man_path = Path(d) / "emotions__Qwen__Qwen2.5-1.5B-Instruct.json"
            man = json.loads(man_path.read_text())
            man['selected']['mean_token_norm_train'] = float('nan')
            man_path.write_text(json.dumps(man))
            with self.assertRaises(ProfileError):
                resolve_vector(good, d)

    def test_profile_response_labels_payload_as_bound_template(self):
        r = build_profile({"model_id": "Qwen/Qwen2.5-1.5B-Instruct", "concept": "calm", "strength": 0.1, "opt_in": True}, EXP)
        self.assertIn("bound_template", r["payload_kind"])
        self.assertNotIn("vector_path", r["ibm_steer_payload"])
