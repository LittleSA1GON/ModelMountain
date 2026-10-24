import json
import tempfile
import unittest
from pathlib import Path

from model_mountain.remote_models import (KAGGLE_GPUS, GPUSpec, ModelPolicyError, ModelRegistry, ModelSpec,
                                          capability_matrix, compatibility, plan_download, spec_from_hf_config,
                                          validate_model_id)

SHA = "a" * 40
ROOT = Path(__file__).resolve().parents[1]


def qwen15(**kw):
    base = dict(model_id="Qwen/Qwen2.5-1.5B-Instruct", revision=SHA, architecture="Qwen2ForCausalLM",
                params_billion=1.54, hidden_size=1536, num_layers=28, num_attention_heads=12,
                max_position_embeddings=32768)
    base.update(kw)
    return ModelSpec(**base)


class ModelIdAndRevisionTests(unittest.TestCase):
    def test_rejects_unsafe_ids(self):
        for bad in ["../etc/passwd", "noslash", "a/b/c", "a/..", "", "a/b;rm -rf", "a/" + "x" * 200]:
            with self.assertRaises(ModelPolicyError, msg=bad):
                validate_model_id(bad)

    def test_requires_commit_sha_not_branch(self):
        for rev in ["main", "v1.0", "a" * 39, "G" * 40]:
            with self.assertRaises(ModelPolicyError):
                qwen15(revision=rev)

    def test_refuses_trust_remote_code(self):
        with self.assertRaises(ModelPolicyError):
            qwen15(trust_remote_code=True)

    def test_config_with_auto_map_refused(self):
        with self.assertRaises(ModelPolicyError):
            spec_from_hf_config("org/m", SHA, {"architectures": ["X"], "auto_map": {"AutoModel": "x.Y"},
                                               "hidden_size": 8, "num_hidden_layers": 2, "num_attention_heads": 2},
                                params_billion=0.1)

    def test_spec_from_config_reads_text_config(self):
        s = spec_from_hf_config("org/m", SHA, {"architectures": ["LlamaForCausalLM"], "text_config": {
            "hidden_size": 64, "num_hidden_layers": 4, "num_attention_heads": 4, "max_position_embeddings": 512,
            "torch_dtype": "float16"}}, params_billion=0.1)
        self.assertEqual((s.hidden_size, s.num_layers, s.dtype), (64, 4, "float16"))

    def test_missing_field_is_explicit(self):
        with self.assertRaises(ModelPolicyError):
            spec_from_hf_config("org/m", SHA, {"architectures": ["LlamaForCausalLM"]}, params_billion=0.1)


class CompatibilityTests(unittest.TestCase):
    def test_small_model_fits_t4_with_fp16_warning(self):
        r = compatibility(qwen15(), KAGGLE_GPUS["T4x2"])
        self.assertTrue(r["compatible"], r["blockers"])
        self.assertEqual(r["runtime_dtype"], "float16")
        self.assertTrue(any("bf16" in w for w in r["warnings"]))
        self.assertEqual(r["evidence_type"], "STATIC_ESTIMATE")

    def test_p100_blocked_by_compute_capability(self):
        r = compatibility(qwen15(), KAGGLE_GPUS["P100"])
        self.assertFalse(r["compatible"])
        self.assertTrue(any("sm60" in b for b in r["blockers"]))

    def test_old_driver_blocked(self):
        gpu = GPUSpec("Tesla T4", 15.0, (7, 5), driver_cuda="12.4")
        self.assertFalse(compatibility(qwen15(), gpu)["compatible"])

    def test_8b_needs_tensor_parallel(self):
        big = qwen15(model_id="ibm-granite/granite-3.1-8b-instruct", architecture="GraniteForCausalLM",
                     params_billion=8.17, hidden_size=4096, num_layers=40, num_attention_heads=32)
        self.assertFalse(compatibility(big, KAGGLE_GPUS["T4x2"], tensor_parallel=1)["compatible"])
        self.assertTrue(compatibility(big, KAGGLE_GPUS["T4x2"], tensor_parallel=2)["compatible"])

    def test_context_and_tp_validation(self):
        phi = qwen15(model_id="microsoft/Phi-3-mini-4k-instruct", architecture="Phi3ForCausalLM",
                     max_position_embeddings=4096)
        self.assertFalse(compatibility(phi, KAGGLE_GPUS["T4x2"], max_model_len=8192)["compatible"])
        self.assertFalse(compatibility(qwen15(), KAGGLE_GPUS["T4x2"], tensor_parallel=3)["compatible"])

    def test_unknown_architecture_blocked_not_downgraded(self):
        r = compatibility(qwen15(architecture="MambaForCausalLM"), KAGGLE_GPUS["T4x2"])
        self.assertFalse(r["compatible"])


class CapabilityMatrixTests(unittest.TestCase):
    def test_artifact_bound_only_where_shipped(self):
        m = capability_matrix(qwen15())
        self.assertTrue(m["capture_hs"]["available"] and m["steer"]["available"])
        self.assertTrue(m["hnode_hallucination"]["available"])
        self.assertFalse(m["attention_tracker"]["available"])
        self.assertIn("artifact", m["attention_tracker"]["reason"])

    def test_upstream_attention_tracker_for_qwen2(self):
        m = capability_matrix(qwen15(model_id="Qwen/Qwen2-1.5B-Instruct"))
        self.assertTrue(m["attention_tracker"]["available"])
        self.assertEqual(m["attention_tracker"]["config_source"], "attention_tracker/Qwen2-1.5B-Instruct.json")


class DownloadPlanTests(unittest.TestCase):
    sib = [{"rfilename": "config.json", "size": 1000}, {"rfilename": "model.safetensors", "size": 3 * 2**30},
           {"rfilename": "tokenizer.json", "size": 5000}, {"rfilename": "pytorch_model.bin", "size": 3 * 2**30},
           {"rfilename": "modeling_custom.py", "size": 100}]

    def test_safetensors_only_and_rejections_recorded(self):
        p = plan_download("Qwen/Qwen2.5-1.5B-Instruct", SHA, self.sib)
        self.assertIn("model.safetensors", p.files)
        self.assertNotIn("pytorch_model.bin", p.files)
        self.assertIn("modeling_custom.py", p.rejected_files)
        self.assertEqual(p.snapshot_kwargs("/c")["revision"], SHA)
        self.assertFalse({"token", "use_auth_token"} & set(p.snapshot_kwargs("/c")))

    def test_pickle_only_repo_refused(self):
        with self.assertRaises(ModelPolicyError):
            plan_download("org/m", SHA, [{"rfilename": "config.json"}, {"rfilename": "pytorch_model.bin"}])

    def test_traversal_and_size_limits(self):
        with self.assertRaises(ModelPolicyError):
            plan_download("org/m", SHA, [{"rfilename": "../x.safetensors"}])
        with self.assertRaises(ModelPolicyError):
            plan_download("org/m", SHA, self.sib, max_total_gib=1)
        with self.assertRaises(ModelPolicyError):
            plan_download("org/m", "main", self.sib)


class RegistryTests(unittest.TestCase):
    def test_revision_conflict_and_allowlist(self):
        reg = ModelRegistry([qwen15()])
        with self.assertRaises(ModelPolicyError):
            reg.register(qwen15(revision="b" * 40))
        with self.assertRaises(ModelPolicyError):
            reg.get("evil/model")

    def test_roundtrip_and_matrix(self):
        reg = ModelRegistry([qwen15()])
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "allow.json"
            f.write_text(reg.to_json())
            rows = ModelRegistry.from_file(str(f)).matrix(KAGGLE_GPUS["T4x2"])
        self.assertEqual(rows[0]["model_id"], "Qwen/Qwen2.5-1.5B-Instruct")
        self.assertIn("capabilities", rows[0])

    def test_shipped_candidates_are_valid_specs_once_pinned(self):
        cands = json.loads((ROOT / "kaggle" / "model_candidates.json").read_text())
        full = [c for c in cands if "hidden_size" in c]   # new candidates get dims from config.json at pin time
        self.assertTrue(any(c["model_id"].startswith("google/gemma-4") for c in cands))
        self.assertTrue(any("granite-4.0" in c["model_id"] for c in cands))
        reg = ModelRegistry([ModelSpec(revision=SHA, **c) for c in full])
        self.assertGreaterEqual(len(reg.items()), 5)
        for row in reg.matrix(KAGGLE_GPUS["T4x2"]):
            self.assertTrue(row["compatible"], (row["model_id"], row["blockers"]))


if __name__ == "__main__":
    unittest.main()


class KernelBuildV2Tests(unittest.TestCase):
    def test_slug_and_configs(self):
        import importlib.util, pathlib
        p = pathlib.Path(__file__).resolve().parents[1] / "kaggle" / "build_kernel.py"
        spec = importlib.util.spec_from_file_location("build_kernel", p)
        bk = importlib.util.module_from_spec(spec); spec.loader.exec_module(bk)
        self.assertEqual(bk.model_slug("google/gemma-4-E2B-it"), "mm-google-gemma-4-e2b-it")
        self.assertLessEqual(len(bk.model_slug("x/" + "a" * 80)), 50)
        g = bk.kernel_config(kind="model", model="google/gemma-4-E2B-it")
        self.assertEqual(g["dtypes"], ["float16"])
        self.assertTrue(g["engine_kwargs"]["enforce_eager"])
        self.assertIn("kaggle/t4_gemma_patches.py", bk.FILES)
        dc = bk.demo_config()
        self.assertEqual(dc["kind"], "demo")
        self.assertIn("google/gemma-4-E4B-it", dc["models"])
        self.assertIn("limit_mm_per_prompt", g["engine_kwargs"])
        q = bk.kernel_config(kind="model", model="Qwen/Qwen2.5-1.5B-Instruct")
        self.assertNotIn("dtypes", q)
        self.assertTrue(all(abs(s) <= 0.5 for s in q["strengths"]))   # paper range: fraction of residual norm
        s = bk.kernel_config(kind="stories")
        self.assertEqual(s["kind"], "stories")
        self.assertFalse(any("evaluation_v1" in f for f in bk.FILES))
        for f in bk.FILES:
            self.assertTrue((p.parents[1] / f).exists() or f.endswith("model_allowlist.json"), f)
