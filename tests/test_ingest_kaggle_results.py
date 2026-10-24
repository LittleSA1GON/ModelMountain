import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.ingest_kaggle_results import LIVE, PROJECT_ID, _clip, attack_pair, ingest, pinned_spec, verified_phase, verify_heads, verify_vectors


class ResultIngestTests(unittest.TestCase):
    model = "Qwen/Qwen2.5-1.5B-Instruct"

    def test_only_successful_bound_phase_is_accepted(self):
        spec = pinned_spec(self.model)
        doc = {"project_id": PROJECT_ID, "evidence_type": LIVE, "model_id": self.model, "revision": spec.revision}
        with tempfile.TemporaryDirectory() as tmp:
            res = Path(tmp)
            path = res / "emotions__Qwen__Qwen2.5-1.5B-Instruct.json"
            path.write_text(json.dumps(doc))
            phase = {"phase": "emotions", "model": self.model, "rc": 0}
            self.assertEqual(verified_phase(res, "emotions", self.model, [phase]), doc)
            self.assertIsNone(verified_phase(res, "emotions", self.model, []))
            self.assertIsNone(verified_phase(res, "emotions", self.model, [{**phase, "rc": 1}]))
            for field, value in (("project_id", "other"), ("revision", "0" * 40),
                                 ("model_id", "ibm-granite/granite-3.1-2b-instruct"),
                                 ("evidence_type", "CPU_SYNTHETIC")):
                path.write_text(json.dumps({**doc, field: value}))
                with self.assertRaises(ValueError):
                    verified_phase(res, "emotions", self.model, [phase])

    def test_vector_binding_and_local_hash_are_required(self):
        spec = pinned_spec(self.model)
        with tempfile.TemporaryDirectory() as tmp:
            res = Path(tmp)
            path = res / "vectors" / self.model.replace("/", "__") / "calm__L18.pt"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"fixture-only direction file; not a real tensor")
            artifact = {"model_id": self.model, "revision": spec.revision, "hidden_size": spec.hidden_size,
                        "evidence_type": LIVE, "block": 18, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "path": "/kaggle/working/mm_results/vectors/Qwen__Qwen2.5-1.5B-Instruct/calm__L18.pt"}
            manifest = {"model_id": self.model, "artifacts": [artifact]}
            verify_vectors(manifest, res)  # byte integrity only; no claim that this fixture is an activation
            for field, value in (("revision", "0" * 40), ("block", 999), ("hidden_size", 2), ("sha256", "0" * 64)):
                with self.assertRaises(ValueError):
                    verify_vectors({**manifest, "artifacts": [{**artifact, field: value}]}, res)
            path.write_bytes(b"replaced")
            with self.assertRaises(ValueError):
                verify_vectors(manifest, res)

    def test_known_secret_forms_are_redacted_before_public_excerpt(self):
        self.assertEqual(_clip("failure hf_" + "x" * 30), "failure [REDACTED]")

    def test_paired_attack_counts_use_lower_is_better_direction(self):
        p = attack_pair({"mean_diff": 0.1, "improved": 20, "worse": 4, "ties": 100})
        self.assertEqual(p["attacks_newly_successful"], 20)
        self.assertEqual(p["attacks_prevented"], 4)
        self.assertNotIn("improved", p)
        self.assertIn("positive is worse", p["direction"])

    def test_operator_source_record_must_bind_the_exact_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = Path(tmp)
            summary = res / "summary.json"
            summary.write_text(json.dumps({"project_id": PROJECT_ID, "kind": "stories", "models": []}))
            (res / "preflight.json").write_text(json.dumps({"project_id": PROJECT_ID}))
            record = {"project_id": PROJECT_ID, "provenance_type": "OPERATOR_RECORD", "kernel_ref": "fixture/job",
                      "kernel_version": 1, "summary_sha256": hashlib.sha256(summary.read_bytes()).hexdigest()}
            (res / "source_run.json").write_text(json.dumps(record))
            self.assertEqual(ingest(res)["kernel"], "fixture/job")
            summary.write_text(summary.read_text() + "\n")
            with self.assertRaises(ValueError):
                ingest(res)

    def test_head_configuration_requires_hash_model_binding_and_valid_indices(self):
        spec = pinned_spec(self.model)
        with tempfile.TemporaryDirectory() as tmp:
            res = Path(tmp)
            path = res / "attention_heads" / (self.model.replace("/", "__") + ".json")
            path.parent.mkdir()
            config = {"model_info": {"model_id": self.model, "revision": spec.revision},
                      "params": {"important_heads": [[1, 2]]}}
            doc = {"model_id": self.model, "n_important_heads": 1}
            for heads, valid in (([[1, 2]], True), ([[1, 9999]], False), ([[1, True]], False)):
                config["params"]["important_heads"] = heads
                path.write_text(json.dumps(config))
                doc["config_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                if valid:
                    verify_heads(doc, res)
                else:
                    with self.assertRaises(ValueError):
                        verify_heads(doc, res)
            doc["config_sha256"] = "0" * 64
            with self.assertRaises(ValueError):
                verify_heads(doc, res)


if __name__ == "__main__":
    unittest.main()
