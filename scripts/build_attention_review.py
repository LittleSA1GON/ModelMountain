"""Build a private head-only diagnostic using canonical prompts and IBM's analyzer in FP32.

This changes analysis precision only. It never reruns or selects protection/steering conditions.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_builder_spec = importlib.util.spec_from_file_location("model_mountain_kernel_builder", ROOT / "kaggle/build_kernel.py")
_builder = importlib.util.module_from_spec(_builder_spec)
_builder_spec.loader.exec_module(_builder)
build, demo_config = _builder.build, _builder.demo_config


REVIEW = r'''
# Independent analysis-precision review. IBM model execution and Q/K capture are unchanged.
_original_engine = _engine
_review_stats = {}

def _engine(worker, config, analyzer=None):
    spec, eng, comp = _original_engine(worker, config, analyzer)
    if worker == "capture_qk":
        import torch
        original = eng.llm.analyzer.compute_attention_from_qk
        stats = {"input_tensors": 0, "input_dtypes": {}, "max_abs_input": 0.0,
                 "attention_tensors": 0, "all_raw_finite": True, "all_attention_finite": True}
        _review_stats[spec.model_id] = stats
        def promote(value):
            if isinstance(value, torch.Tensor) and value.is_floating_point():
                if not bool(torch.isfinite(value).all()):
                    stats["all_raw_finite"] = False
                    raise RuntimeError("Non-finite raw Q/K capture; FP32 analysis cannot repair it")
                dtype = str(value.dtype)
                stats["input_dtypes"][dtype] = stats["input_dtypes"].get(dtype, 0) + 1
                stats["input_tensors"] += 1
                if value.numel():
                    stats["max_abs_input"] = max(stats["max_abs_input"], float(value.abs().max()))
                return value.float()
            if isinstance(value, dict):
                return {k: promote(v) for k, v in value.items()}
            if isinstance(value, list):
                return [promote(v) for v in value]
            if isinstance(value, tuple):
                return tuple(promote(v) for v in value)
            return value
        def analyze_fp32(run_id=None, probes=None):
            if probes is None:
                raise RuntimeError("Review requires in-memory captured probes")
            result = original(run_id, probes=promote(probes))
            for prompt in result or []:
                for layer in prompt.values():
                    stats["attention_tensors"] += 1
                    if not bool(torch.isfinite(layer["attention"]).all()):
                        stats["all_attention_finite"] = False
                        raise RuntimeError("Non-finite IBM attention result after FP32 promotion")
            return result
        eng.llm.analyzer.compute_attention_from_qk = analyze_fp32
    return spec, eng, comp

_original_heads = phase_heads
def phase_heads_review():
    _original_heads()
    import hashlib
    model = CONFIG["model"]
    key = model.replace("/", "__")
    path = os.path.join(OUT, f"heads__{key}.json")
    record = json.load(open(path))
    record["analysis_review"] = {"method": "Captured Q/K promoted to FP32 before IBM's original attention analyzer",
        "source_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
        "prompt_protocol": "Unchanged canonical behavior_tests document groups and head selection",
        "stats": _review_stats.get(model), "security_effectiveness_measured": False}
    write(f"heads__{key}.json", record)

PHASES["heads"] = phase_heads_review

def main():
    unpack()
    if "--phase" in sys.argv:
        os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
        model = sys.argv[sys.argv.index("--model") + 1]
        CONFIG["model"] = model
        CONFIG.update(CONFIG.get("per_model", {}).get(model, {}))
        os.environ.update(CONFIG.get("env", {}))
        PHASES["heads"]()
        return
    summary = {"kind": "attention_review", "models": CONFIG["models"], "config": CONFIG,
               "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "phases": []}
    try:
        usable, blockers = phase_preflight()
    except Exception:
        usable, blockers = False, [traceback.format_exc()[-2000:]]
    summary["preflight_usable"], summary["preflight_blockers"] = usable, blockers
    if usable:
        for model in CONFIG["models"]:
            summary["phases"].append(run_child("heads", model))
            write("summary.json", {**summary, "partial": True})
            drop_weights(model)
    summary["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write("summary.json", summary)
'''


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True)
    args = parser.parse_args()
    config = demo_config()
    config["kind"] = "attention_review"
    out = build(args.owner, config, slug="model-mountain-attention-review")
    run = out / "run.py"
    source = run.read_text(encoding="utf-8")
    marker = '\nif __name__ == "__main__":'
    if source.count(marker) != 1:
        raise ValueError("Canonical driver entry changed; inspect before adapting")
    source = source.replace(marker, "\n" + REVIEW + marker)
    ast.parse(source)
    run.write_text(source, encoding="utf-8", newline="\n")
    metadata_path = out / "kernel-metadata.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["title"] = "Model Mountain attention review"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    manifest_path = out / "BUNDLE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["run_py_sha256"] = hashlib.sha256(source.encode()).hexdigest()
    manifest["review_method"] = "FP32 promotion of captured Q/K into unmodified IBM attention analyzer"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(out)


if __name__ == "__main__":
    main()
