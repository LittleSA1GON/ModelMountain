"""Build a private two-prompt integration check from the complete current MIA kernel.

No helper is copied out of the runtime. This smoke check does not fit a vector or
measure security; its generated code uses the same registry and engine as the study.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "kaggle"))
from build_kernel import build, kernel_config

PHASE = '''
def phase_integration_smoke():
    import hashlib
    import numpy as np
    from model_mountain.remote_models import IBM_MIA_COMMIT
    spec = registry().get(CONFIG["model"])
    layers = [1, spec.num_layers]
    spec, engine, comp = _engine("capture_hs", {"hidden_states": {"layers": layers, "mode": "last_token"}}, analyzer="hidden_states")
    prompts = ["What is 2 + 2?", "What is the capital of France?"]
    captures, evidence = engine.capture(prompts, layers, batch=1)
    artifact = os.path.join(OUT, "capture_check.npz")
    np.savez_compressed(artifact, hidden_states=captures)
    outputs, timing = engine.generate(prompts, steer=None, max_tokens=32)
    write("capture_check.json", {"status": "capture_reported", "evidence_type": "REAL_IBM_MIA",
          "model_id": spec.model_id, "model_revision": spec.revision, "ibm_revision": IBM_MIA_COMMIT,
          "model_executed": True, "mia_hook_executed": True, "independently_verified": False,
          "capture_evidence": evidence, "compatibility": comp, "outputs": outputs, "timing": timing,
          "artifact_sha256": hashlib.sha256(open(artifact, "rb").read()).hexdigest(),
          "limitations": ["Two-prompt integration smoke only. No emotion vector, intervention, attention or security effectiveness measured."]})

PHASES["integration_smoke"] = phase_integration_smoke
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True)
    args = parser.parse_args()
    config = kernel_config(kind="model", model="Qwen/Qwen2.5-1.5B-Instruct",
                           extra={"max_model_len": 1024, "gpu_memory_utilization": 0.60,
                                  "phase_timeout": 1800})
    config.setdefault("env", {})["MIA_APERTURE_GPU_BYTES"] = str(512 * 1024**2)
    folder = build(args.owner, config, slug="model-mountain-capture-check-20261024")
    metadata_path = folder / "kernel-metadata.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["title"] = "Model Mountain Capture Check 20261024"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    path = folder / "run.py"
    code = path.read_text(encoding="utf-8")
    original = '            run_model(CONFIG["model"], summary)'
    assert code.count(original) == 1, "Runtime main changed; re-review the smoke adapter"
    code = code.replace(original, '            summary["phases"].append(run_child("integration_smoke", CONFIG["model"]))')
    entry = 'if __name__ == "__main__":\n    main()'
    assert code.count(entry) == 1
    code = code.replace(entry, PHASE + "\n" + entry)
    # Keep full private error evidence if the runtime has not yet added log retention.
    if '"stdout_log"' not in code:
        anchor = '    rec = {"phase": phase, "model": model, "rc": rc'
        assert code.count(anchor) == 1
        logging = ('    os.makedirs(os.path.join(OUT, "logs"), exist_ok=True)\n'
                   '    with open(os.path.join(OUT, "logs", phase + ".log"), "w") as phase_log:\n'
                   '        phase_log.write(out + "\\nSTDERR\\n" + err)\n')
        code = code.replace(anchor, logging + anchor)
    ast.parse(code)
    path.write_text(code, encoding="utf-8", newline="\n")
    manifest_path = folder / "BUNDLE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.update(run_py_sha256=hashlib.sha256(code.encode()).hexdigest(),
                    purpose="Two-prompt capture integration check; no steering or safety claim")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(folder)


if __name__ == "__main__":
    main()
