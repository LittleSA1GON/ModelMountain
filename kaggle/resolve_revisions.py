"""Pin Hugging Face revisions for kaggle/model_candidates.json -> kaggle/model_allowlist.json.

Run on a machine with internet access to huggingface.co (e.g. the owner's PC):
    .venv\\Scripts\\python.exe kaggle\\resolve_revisions.py
    .venv\\Scripts\\python.exe kaggle\\resolve_revisions.py --add org/model --params-billion 2.0

For each model: resolve the current commit SHA, fetch config.json at that SHA, verify the
declared dimensions match, plan a safetensors-only download, and write the pinned spec.
Gated repos need HF_TOKEN in the environment (read by huggingface_hub, never written here).
Any mismatch or policy refusal aborts that model with an explicit reason.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from model_mountain.remote_models import (ModelPolicyError, ModelSpec, plan_download,  # noqa: E402
                                          spec_from_hf_config)

CHECK = ("architecture", "hidden_size", "num_layers", "num_attention_heads", "max_position_embeddings")


def resolve(candidate: dict, api) -> tuple[dict, dict]:
    mid = candidate["model_id"]
    info = api.model_info(mid, files_metadata=True)
    sha = info.sha
    from huggingface_hub import hf_hub_download
    cfg = json.loads(Path(hf_hub_download(mid, "config.json", revision=sha)).read_text())
    siblings = [{"rfilename": s.rfilename, "size": s.size} for s in info.siblings]
    plan = plan_download(mid, sha, siblings, gated=bool(getattr(info, "gated", False)))
    spec = spec_from_hf_config(mid, sha, cfg, params_billion=candidate["params_billion"],
                               license=candidate.get("license", "unknown"),
                               gated=bool(getattr(info, "gated", False)))
    mism = {k: (candidate[k], getattr(spec, k)) for k in CHECK if k in candidate and candidate[k] != getattr(spec, k)}
    if mism:
        raise ModelPolicyError(f"{mid}: declared dims differ from config.json at {sha}: {mism}")
    spec = ModelSpec(**{**asdict(spec), "notes": candidate.get("notes", "")})
    return asdict(spec), {"files": len(plan.files), "gib": round(plan.total_bytes / 2**30, 2),
                          "rejected": list(plan.rejected_files)}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--candidates", default=str(ROOT / "kaggle" / "model_candidates.json"))
    p.add_argument("--output", default=str(ROOT / "kaggle" / "model_allowlist.json"))
    p.add_argument("--add", help="extra model id to append to candidates (dims read from config.json)")
    p.add_argument("--params-billion", type=float)
    a = p.parse_args()
    from huggingface_hub import HfApi
    api = HfApi()
    cands = json.loads(Path(a.candidates).read_text())
    if a.add:
        if not a.params_billion:
            p.error("--params-billion is required with --add")
        cands.append({"model_id": a.add, "params_billion": a.params_billion})
    pinned, report = [], {}
    for c in cands:
        try:
            spec, plan = resolve(c, api)
            pinned.append(spec)
            report[c["model_id"]] = {"revision": spec["revision"], **plan}
        except Exception as exc:  # explicit, per-model
            report[c["model_id"]] = {"error": f"{type(exc).__name__}: {exc}"[:400]}
    Path(a.output).write_text(json.dumps(pinned, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if pinned else 1


if __name__ == "__main__":
    raise SystemExit(main())
