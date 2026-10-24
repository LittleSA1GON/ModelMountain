"""User-adjustable steering profiles bound to REAL vectors, plus a preview from measured Kaggle runs.

A user picks: model, concept (an emotion vector discovered for that model), strength (fraction of the mean residual
norm at the steered layer, the unit used by arXiv 2604.07729), optionally a different decoder block, phase and
positions. ``build_profile`` validates the choice, binds it to the exact vector artifact (model revision + block +
sha256) found in ``api/experiments.json``, and returns the IBM vLLM-Hook ``steer`` payload a GPU worker would run.

Nothing here runs a model. ``preview`` returns the measured outcome at the nearest strength that was actually run on
Kaggle, labeled with its evidence type; strengths that were never measured are reported as such.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "api" / "experiments.json"
MAX_ABS_STRENGTH = 0.5          # beyond this the paper reports incoherent text; refuse rather than clamp silently
# Starting points motivated by arXiv 2604.07729 (calm reduced, desperation increased misaligned behavior in the paper's
# model). They are UNVALIDATED for these small models until the Kaggle protect/steer phases measure them.
EXPERIMENTAL_PRESETS = {"calm": 0.1, "desperate": -0.1}


class ProfileError(ValueError):
    pass


def load_experiments(path: Path | None = None) -> dict | None:
    p = Path(path) if path else EXPERIMENTS
    if not p.is_file():
        return None
    doc = json.loads(p.read_text(encoding="utf-8"))
    if doc.get("project_id") != "16f864bfa1303fc9" or doc.get("schema") != "mm-experiments-v1":
        raise ProfileError("experiments file has the wrong project or schema")
    return doc


def catalog(experiments: dict | None) -> dict:
    """What the steering editor can offer, per model: real vectors (if captured) and attention heads."""
    from .remote_models import ModelRegistry
    # kaggle/ is excluded from the Vercel bundle; api/model_allowlist.json is the sanitized copy of the pinned specs.
    reg_path = next((p for p in (ROOT / "kaggle" / "model_allowlist.json", ROOT / "api" / "model_allowlist.json") if p.is_file()), None)
    reg = ModelRegistry.from_file(str(reg_path)) if reg_path else None
    wanted = ["Qwen/Qwen2.5-1.5B-Instruct", "ibm-granite/granite-3.1-2b-instruct", "google/gemma-4-E4B-it", "google/gemma-4-E2B-it"]
    measured = {m["model_id"]: m for m in (experiments or {}).get("models", [])}
    rows = []
    for mid in wanted:
        m = measured.get(mid)
        spec = None
        try:
            spec = reg.get(mid) if reg else None
        except Exception:
            spec = None
        if m is None and mid == "google/gemma-4-E2B-it":
            continue                       # fallback model only listed when it actually ran
        em = (m or {}).get("emotions") or {}
        rows.append({
            "model_id": mid, "revision": (m or {}).get("revision") or (spec.revision if spec else None),
            "num_layers": spec.num_layers if spec else None, "hidden_size": spec.hidden_size if spec else None,
            "status": (m or {}).get("status", "not_run"),
            "vectors": [{"concept": v["concept"], "block": v["block"], "sha256": v["sha256"]} for v in em.get("vectors", [])],
            "selected_block": em.get("selected_block"), "mean_token_norm_train": em.get("mean_token_norm_train"),
            "test_accuracy": em.get("test_accuracy"), "chance": em.get("chance"),
            "heads": (m or {}).get("heads"), "attn": (m or {}).get("attn"),
            "measured_strengths": sorted({r["strength"] for r in ((m or {}).get("steer") or {}).get("rows", [])}),
            "evidence_type": "REAL_IBM_MIA" if em else "NOT_CAPTURED",
        })
    return {"models": rows, "experimental_presets": EXPERIMENTAL_PRESETS,
            "presets_note": "Starting points from the emotion-vector paper; no protective effect is claimed until measured here.",
            "max_abs_strength": MAX_ABS_STRENGTH,
            "units": "strength x mean residual-token norm at the steered block (train stories only)",
            "methods": ["add_vector"], "phases": ["both", "prefill", "decode"], "positions": ["all_tokens", "last_token"]}


def build_profile(body: dict, experiments: dict | None) -> dict:
    if not isinstance(body, dict):
        raise ProfileError("profile must be a JSON object")
    allowed = {"model_id", "concept", "strength", "block", "phase", "positions", "method", "opt_in"}
    if set(body) - allowed:
        raise ProfileError("unsupported profile fields: " + ", ".join(sorted(set(body) - allowed)))
    for key in ("model_id", "concept"):
        if not isinstance(body.get(key), str) or not 1 <= len(body[key]) <= 100:
            raise ProfileError(f"{key} must be a non-empty string")
    if body.get("opt_in") is not True:
        raise ProfileError("steering is opt-in: set opt_in=true to build a profile")
    strength = body.get("strength")
    if type(strength) not in (int, float) or not math.isfinite(strength) or abs(strength) > MAX_ABS_STRENGTH:
        raise ProfileError(f"strength must be a finite number within +/-{MAX_ABS_STRENGTH}")
    method, phase, positions = body.get("method", "add_vector"), body.get("phase", "both"), body.get("positions", "all_tokens")
    if method != "add_vector" or phase not in ("both", "prefill", "decode") or positions not in ("all_tokens", "last_token"):
        raise ProfileError("unsupported method/phase/positions")
    cat = {m["model_id"]: m for m in catalog(experiments)["models"]}
    model = cat.get(body.get("model_id"))
    if model is None:
        raise ProfileError("model is not one of the evaluated models")
    concept = body.get("concept")
    vec = next((v for v in model["vectors"] if v["concept"] == concept), None)
    default_block = vec["block"] if vec else model.get("selected_block")
    if default_block is None and model.get("num_layers"):
        default_block = int(round(model["num_layers"] * 2 / 3))      # paper-style ~2/3 depth until a vector exists
    block = body.get("block", default_block)
    if model.get("num_layers") is not None and (type(block) is not int or not 0 <= block < model["num_layers"]):
        raise ProfileError(f"block must be an integer decoder index in [0, {model['num_layers'] - 1}]")
    status, payload, coefficient = "vector_not_captured_yet", None, None
    if vec is not None and model.get("mean_token_norm_train"):
        coefficient = float(strength) * float(model["mean_token_norm_train"])
        payload = {"method": method, "coefficient": coefficient, "optimal_layer": block, "phase": phase,
                   "positions": positions, "vector_sha256": vec["sha256"]}
        status = "bound_to_real_vector" if block == vec["block"] else "bound_off_layer_unvalidated"
    profile = {"model_id": model["model_id"], "model_revision": model.get("revision"), "concept": concept,
               "strength": float(strength), "block": block, "method": method, "phase": phase, "positions": positions,
               "vector_sha256": vec["sha256"] if vec else None, "coefficient": coefficient}
    digest = sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()
    measured_block = vec["block"] if vec else None
    return {"profile": profile, "profile_sha256": digest, "status": status, "ibm_steer_payload": payload,
            "payload_kind": "bound_template: the GPU worker resolves vector_sha256 to a verified vector_path "
                            "(python -m model_mountain.steering_lab apply)" if payload else None,
            "preview": preview(experiments, model["model_id"], concept, float(strength), block=block, phase=phase,
                               positions=positions, measured_block=measured_block),
            "runs_on": "GPU worker with IBM vLLM-Hook (MIA worker 'steer'); not executed by this API",
            "note": ("The vector was fitted at block %s; steering a different block was not validated." % vec["block"])
                    if vec and block != vec["block"] else None}


def preview(experiments: dict | None, model_id: str, concept: str, strength: float, *, block=None, phase="both",
            positions="all_tokens", measured_block=None) -> dict:
    """Measured result at the nearest strength actually run on Kaggle for this model/concept (if any).

    The Kaggle sweep steered the vector's own block, both phases, all tokens. Any other setting is reported as
    'reference_condition_differs': the numbers describe the reference condition, not the requested one.
    """
    m = next((x for x in (experiments or {}).get("models", []) if x["model_id"] == model_id), None)
    rows = [r for r in ((m or {}).get("steer") or {}).get("rows", []) if r.get("emotion") == concept]
    if not rows:
        return {"status": "not_measured", "evidence_type": "NOT_CAPTURED"}
    differs = [k for k, ok in (("block", block is None or measured_block is None or block == measured_block),
                               ("phase", phase == "both"), ("positions", positions == "all_tokens")) if not ok]
    best = min(rows, key=lambda r: (abs(r["strength"] - strength), -abs(r["strength"])))
    status = ("reference_condition_differs" if differs else
              "measured" if math.isclose(best["strength"], strength, abs_tol=1e-9) else "nearest_measured")
    return {"status": status, "differs_in": differs, "reference_condition": {"block": measured_block, "phase": "both",
            "positions": "all_tokens"}, "measured_strength": best["strength"], "requested_strength": strength,
            "result": best, "baseline": m["steer"].get("baseline"), "evidence_type": "REAL_IBM_MIA"}


# ---------------------------------------------------------------------------------------- GPU-side application
def resolve_vector(profile: dict, vectors_dir: str | Path, *, allow_off_layer: bool = False) -> dict:
    """Find the vector file whose sha256 matches the profile, verify it, and return a complete IBM steer config.

    Runs where the Kaggle vector files live (a GPU worker). Refuses: unknown hash, hidden-size mismatch,
    off-layer steering unless explicitly allowed (it was not validated).
    """
    want = profile.get("vector_sha256")
    if not want or profile.get("coefficient") is None:
        raise ProfileError("profile is not bound to a captured vector")
    from .mia_runtime import sha256_file
    hits = [p for p in Path(vectors_dir).rglob("*.pt") if sha256_file(p) == want]
    if not hits:
        raise ProfileError("no vector file with the profile's sha256 under " + str(vectors_dir))
    path = hits[0]
    m = re.search(r"__L(\d+)\.pt$", path.name)
    fitted_block = int(m.group(1)) if m else None
    if fitted_block is not None and profile["block"] != fitted_block and not allow_off_layer:
        raise ProfileError(f"vector was fitted at block {fitted_block}; pass allow_off_layer to steer block {profile['block']}")
    try:
        import torch
        vec = torch.load(str(path), map_location="cpu", weights_only=True)
        dim = int(vec["dir"].numel())
    except Exception as exc:
        raise ProfileError(f"vector file unreadable: {exc!r}") from None
    return {"steer": {"method": profile["method"], "coefficient": float(profile["coefficient"]),
                      "optimal_layer": profile["block"], "phase": profile["phase"], "positions": profile["positions"],
                      "vector_path": str(path)}, "vector_path": str(path), "hidden_size": dim, "fitted_block": fitted_block}


def apply_profile(profile_doc: dict, vectors_dir: str, prompts: list[str], *, allow_off_layer: bool = False,
                  max_tokens: int = 128) -> dict:
    """GPU only: run the same prompts unsteered and steered with IBM MIA and return both outputs side by side."""
    from .mia_runtime import MIAEngine
    from .remote_models import ModelRegistry
    prof = profile_doc.get("profile", profile_doc)
    reg_path = next((q for q in (ROOT / "kaggle" / "model_allowlist.json", ROOT / "api" / "model_allowlist.json") if q.is_file()), None)
    if reg_path is None:
        raise ProfileError("model allowlist missing")
    spec = ModelRegistry.from_file(str(reg_path)).get(prof["model_id"])
    if prof.get("model_revision") and prof["model_revision"] != spec.revision:
        raise ProfileError("profile model revision does not match the pinned model")
    cfg = resolve_vector(prof, vectors_dir, allow_off_layer=allow_off_layer)
    if cfg["hidden_size"] != spec.hidden_size:
        raise ProfileError("vector hidden size does not match the model")
    eng = MIAEngine(spec, worker="steer", config={}, work_dir=str(Path(vectors_dir) / "_cfg"), runtime_dtype="float16",
                    engine_kwargs={"enforce_eager": True})
    base, b_info = eng.generate(prompts, steer=None, max_tokens=max_tokens)
    steered, s_info = eng.generate(prompts, steer=cfg["steer"], max_tokens=max_tokens)
    return {"model_id": spec.model_id, "revision": spec.revision, "steer": cfg["steer"], "prompts": prompts,
            "unsteered": base, "steered": steered, "outputs_differ": sum(a != b for a, b in zip(base, steered)),
            "evidence_type": "REAL_IBM_MIA", "note": "Differences corroborate that steering took effect; not an attestation."}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Apply a Model Mountain steering profile on a GPU worker (IBM vLLM-Hook).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("apply")
    a.add_argument("profile", help="JSON downloaded from the Steering page")
    a.add_argument("--vectors", required=True, help="folder with the Kaggle vectors/ output")
    a.add_argument("--prompt", action="append", required=True)
    a.add_argument("--allow-off-layer", action="store_true")
    r = sub.add_parser("resolve")
    r.add_argument("profile")
    r.add_argument("--vectors", required=True)
    args = ap.parse_args()
    doc = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    if args.cmd == "resolve":
        print(json.dumps(resolve_vector(doc.get("profile", doc), args.vectors), indent=2))
    else:
        print(json.dumps(apply_profile(doc, args.vectors, args.prompt, allow_off_layer=args.allow_off_layer), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
