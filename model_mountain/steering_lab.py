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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "api" / "experiments.json"
MAX_ABS_STRENGTH = 0.5          # beyond this the paper reports incoherent text; refuse rather than clamp silently
# Protection steering: the "injection shield" is each model's own hijack-compliance direction, negated
# (kaggle/run_mia_kaggle.py:phase_shield). Blocks match where each model's vectors were captured on Kaggle.
SHIELD_CONCEPT = "injection_shield"
SHIELD_BLOCKS = {"Qwen/Qwen2.5-1.5B-Instruct": 10, "ibm-granite/granite-3.1-2b-instruct": 26, "google/gemma-4-E4B-it": 16}
SHIELD_DEFAULT_STRENGTH = 0.1


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
        sh = (m or {}).get("shield") or {}
        sa = sh.get("artifact") or {}
        shield_block = sa.get("block", SHIELD_BLOCKS.get(mid))
        protection = [{"concept": SHIELD_CONCEPT, "block": sa["block"], "sha256": sa["sha256"],
                       "mean_token_norm": sa.get("mean_token_norm"), "label": "Injection shield"}] if sa.get("sha256") else []
        chosen = (sh.get("validation") or {}).get("chosen_strength")
        rows.append({
            "model_id": mid, "revision": (m or {}).get("revision") or (spec.revision if spec else None),
            "num_layers": spec.num_layers if spec else None, "hidden_size": spec.hidden_size if spec else None,
            "status": (m or {}).get("status", "not_run"),
            "vectors": [{"concept": v["concept"], "block": v["block"], "sha256": v["sha256"]} for v in em.get("vectors", [])],
            "selected_block": em.get("selected_block"), "mean_token_norm_train": em.get("mean_token_norm_train"),
            "test_accuracy": em.get("test_accuracy"), "chance": em.get("chance"),
            # Attention heads are offered only as a prompt-injection detector (Attention Tracker); they are never steered.
            "heads": (m or {}).get("heads"), "heads_review": (m or {}).get("heads_review"),
            "measured_strengths": sorted({r["strength"] for r in ((m or {}).get("steer") or {}).get("rows", [])}),
            "evidence_type": "REAL_IBM_MIA" if em else "NOT_CAPTURED",
            "protection_vectors": protection,
            "shield": {"status": "measured" if protection else "gpu_run_pending", "block": shield_block,
                       "chosen_strength": chosen, "test": sh.get("test"), "truthfulqa": sh.get("truthfulqa"),
                       "validation": sh.get("validation"), "direction_source": sa.get("direction_source")},
            "mvp_preset": {"concept": SHIELD_CONCEPT, "strength": chosen if isinstance(chosen, (int, float)) else SHIELD_DEFAULT_STRENGTH,
                           "block": shield_block, "phase": "both", "positions": "all_tokens",
                           "label": "Injection shield (protection)"},
        })
    return {"models": rows,
            "presets_note": "MVP preset: the injection shield (each model's own hijack-compliance direction, negated) at the "
                            "strength chosen on Tensor Trust validation; effect measured on held-out attacks.",
            "max_abs_strength": MAX_ABS_STRENGTH,
            "units": "strength x mean residual-token norm at the steered block, measured on the vector's own fitting prompts",
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
    vec = next((v for v in model["vectors"] + model.get("protection_vectors", []) if v["concept"] == concept), None)
    default_block = vec["block"] if vec else (model["shield"]["block"] if concept == SHIELD_CONCEPT else model.get("selected_block"))
    if default_block is None and model.get("num_layers"):
        default_block = int(round(model["num_layers"] * 2 / 3))      # paper-style ~2/3 depth until a vector exists
    block = body.get("block", default_block)
    if model.get("num_layers") is not None and (type(block) is not int or not 0 <= block < model["num_layers"]):
        raise ProfileError(f"block must be an integer decoder index in [0, {model['num_layers'] - 1}]")
    status, payload, coefficient = "vector_not_captured_yet", None, None
    norm = (vec or {}).get("mean_token_norm") or model.get("mean_token_norm_train")
    if vec is not None and norm:
        coefficient = float(strength) * float(norm)
        payload = {"method": method, "coefficient": coefficient, "optimal_layer": block, "phase": phase,
                   "positions": positions, "vector_sha256": vec["sha256"]}
        status = "bound_to_real_vector" if block == vec["block"] else "bound_off_layer_unvalidated"
    profile = {"model_id": model["model_id"], "model_revision": model.get("revision"), "concept": concept,
               "strength": float(strength), "block": block, "method": method, "phase": phase, "positions": positions,
               "vector_sha256": vec["sha256"] if vec else None, "coefficient": coefficient}
    digest = sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()
    measured_block = vec["block"] if vec else None
    return {"profile": profile, "profile_sha256": digest, "status": status, "ibm_steer_payload": payload,
            "payload_kind": "bound_template: a GPU worker resolves vector_sha256 against the run's own manifest "
                            "(python -m model_mountain.steering_lab apply profile.json --results <mm_results> --prompt ...)" if payload else None,
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
    if concept == SHIELD_CONCEPT:
        return _shield_preview(m, strength, block=block, phase=phase, positions=positions)
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


def _shield_preview(m, strength, *, block=None, phase="both", positions="all_tokens") -> dict:
    """Protection preview: held-out Tensor Trust at the validation-chosen strength; other strengths are validation-only."""
    sh = (m or {}).get("shield") or {}
    art, val, test = sh.get("artifact") or {}, sh.get("validation") or {}, sh.get("test") or {}
    if not art or not test:
        return {"status": "not_measured", "kind": "protection", "evidence_type": "NOT_CAPTURED"}
    differs = [k for k, ok in (("block", block is None or block == art.get("block")), ("phase", phase == "both"),
                               ("positions", positions == "all_tokens")) if not ok]
    chosen = val.get("chosen_strength")
    sweep = val.get("sweep") or []
    near = min(sweep, key=lambda r: abs(r["strength"] - strength)) if sweep else None
    at_chosen = chosen is not None and math.isclose(strength, chosen, abs_tol=1e-9)
    status = ("reference_condition_differs" if differs else "measured" if at_chosen else "validation_only")
    return {"status": status, "kind": "protection", "differs_in": differs, "chosen_strength": chosen,
            "requested_strength": strength, "benchmark": "Tensor Trust hijacking (held-out defender groups)",
            "test": test, "truthfulqa": sh.get("truthfulqa"), "validation_nearest": near,
            "validation_bare": {"attack_success": val.get("bare_attack_success"), "access_granted": val.get("bare_access_granted")},
            "utility_constraint_met": val.get("utility_constraint_met"), "evidence_type": "REAL_IBM_MIA"}


# ---------------------------------------------------------------------------------------- GPU-side application
def load_manifest(results_dir: str | Path, model_id: str) -> dict:
    """The Kaggle emotions__<model>.json written by the real capture run (trusted provenance for vectors)."""
    path = Path(results_dir) / f"emotions__{model_id.replace('/', '__')}.json"
    if not path.is_file():
        raise ProfileError(f"no emotions manifest for {model_id} in {results_dir}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if (doc.get("project_id") != "16f864bfa1303fc9" or doc.get("evidence_type") != "REAL_IBM_MIA"
            or doc.get("model_id") != model_id or not doc.get("artifacts")):
        raise ProfileError("emotions manifest is not a REAL_IBM_MIA capture for this model")
    return doc


def _shield_manifest(results_dir: str | Path, model_id: str) -> dict | None:
    path = Path(results_dir) / f"shield__{model_id.replace('/', '__')}.json"
    if not path.is_file():
        return None
    doc = json.loads(path.read_text(encoding="utf-8"))
    art = doc.get("artifact") or {}
    if (doc.get("project_id") != "16f864bfa1303fc9" or doc.get("evidence_type") != "REAL_IBM_MIA"
            or doc.get("model_id") != model_id or art.get("concept") != SHIELD_CONCEPT):
        raise ProfileError("shield manifest is not a REAL_IBM_MIA run for this model")
    return doc


def _pinned_spec(model_id):
    from .remote_models import ModelRegistry, ModelPolicyError
    reg_path = next((p for p in (ROOT / "kaggle/model_allowlist.json", ROOT / "api/model_allowlist.json") if p.is_file()), None)
    if reg_path is None:
        raise ProfileError("model allowlist missing")
    try:
        return ModelRegistry.from_file(str(reg_path)).get(model_id)
    except (ModelPolicyError, KeyError, TypeError, ValueError):
        raise ProfileError("profile model is not pinned in the trusted allowlist") from None


def resolve_vector(profile: dict, results_dir: str | Path, *, allow_off_layer: bool = False) -> dict:
    """Resolve a profile to a verified vector file using the run's own manifest, and build the IBM steer config.

    Every field must match the trusted artifact: model id, pinned revision, concept, sha256 and (unless explicitly
    allowed) the fitted block. The coefficient must be finite and within MAX_ABS_STRENGTH x the run's train norm.
    """
    for key in ("model_id", "model_revision", "concept", "vector_sha256", "block", "coefficient"):
        if profile.get(key) is None:
            raise ProfileError(f"profile field {key} is missing (unbound or edited template)")
    spec = _pinned_spec(profile["model_id"])
    if profile["model_revision"] != spec.revision:
        raise ProfileError("profile revision is not the pinned model revision")
    if type(profile["block"]) is not int or not 0 <= profile["block"] < spec.num_layers:
        raise ProfileError("profile decoder block is outside the pinned model")
    if profile.get("method", "add_vector") != "add_vector" or profile.get("phase") not in ("both", "prefill", "decode") \
            or profile.get("positions") not in ("all_tokens", "last_token"):
        raise ProfileError("unsupported method/phase/positions")
    coef = profile["coefficient"]
    if type(coef) not in (int, float) or not math.isfinite(coef):
        raise ProfileError("coefficient must be a finite number")
    if profile["concept"] == SHIELD_CONCEPT:
        sh = _shield_manifest(results_dir, profile["model_id"])
        if sh is None:
            raise ProfileError(f"no shield manifest for {profile['model_id']} in {results_dir}")
        man = {"revision": sh.get("revision"), "artifacts": [sh["artifact"]],
               "selected": {"mean_token_norm_train": sh["artifact"].get("mean_token_norm")}}
    else:
        man = load_manifest(results_dir, profile["model_id"])
    if man.get("revision") != profile["model_revision"]:
        raise ProfileError("profile revision does not match the capture run's pinned revision")
    art = next((a for a in man["artifacts"] if a.get("sha256") == profile["vector_sha256"]), None)
    if art is None or art.get("concept") != profile["concept"] or art.get("model_id") != profile["model_id"] \
            or art.get("revision") != profile["model_revision"]:
        raise ProfileError("vector hash/concept/model/revision do not match a trusted artifact of this run")
    if profile["block"] != art["block"] and not allow_off_layer:
        raise ProfileError(f"vector was fitted at block {art['block']}; pass allow_off_layer to steer block {profile['block']}")
    norm = (man.get("selected") or {}).get("mean_token_norm_train")
    if type(norm) not in (int, float) or not math.isfinite(norm) or norm <= 0:
        raise ProfileError("capture manifest requires a positive finite train norm")
    if abs(coef) > MAX_ABS_STRENGTH * float(norm) + 1e-9:
        raise ProfileError("coefficient exceeds the allowed strength range for this run")
    from .mia_runtime import sha256_file
    cand = [q for q in Path(results_dir).rglob(Path(str(art.get("path", ""))).name or "*.pt") if q.is_file()]
    path = next((q for q in cand if sha256_file(q) == art["sha256"]), None)
    if path is None:
        raise ProfileError("vector file for the trusted artifact was not found or its sha256 changed")
    try:
        import torch
        vec = torch.load(str(path), map_location="cpu", weights_only=True)
        direction = vec["dir"]
        if direction.ndim != 1 or not direction.is_floating_point() or not bool(torch.isfinite(direction).all()):
            raise ValueError("direction must be a finite floating point vector")
        dim = int(direction.numel())
    except Exception as exc:
        raise ProfileError(f"vector file unreadable: {exc!r}") from None
    if dim != art.get("hidden_size") or dim != spec.hidden_size:
        raise ProfileError("vector size does not match the artifact's hidden size")
    return {"steer": {"method": "add_vector", "coefficient": float(coef), "optimal_layer": profile["block"],
                      "phase": profile["phase"], "positions": profile["positions"], "vector_path": str(path)},
            "vector_path": str(path), "hidden_size": dim, "fitted_block": art["block"], "artifact": art}


def apply_profile(profile_doc: dict, results_dir: str, prompts: list[str], *, allow_off_layer: bool = False,
                  max_tokens: int = 128) -> dict:
    """GPU only: run the same prompts unsteered and steered with IBM MIA and return both outputs side by side."""
    import os
    from .mia_runtime import IBM_MIA_COMMIT, MIAEngine, preflight
    prof = profile_doc.get("profile", profile_doc)
    spec = _pinned_spec(prof["model_id"])
    if prof.get("model_revision") != spec.revision:
        raise ProfileError("profile model revision does not match the pinned model")
    cfg = resolve_vector(prof, results_dir, allow_off_layer=allow_off_layer)
    if cfg["hidden_size"] != spec.hidden_size:
        raise ProfileError("vector hidden size does not match the model")
    if (type(max_tokens) is not int or not 1 <= max_tokens <= 512 or not isinstance(prompts, list)
            or not 1 <= len(prompts) <= 32 or any(not isinstance(p, str) or not p.strip() or len(p) > 8192 for p in prompts)):
        raise ProfileError("1-32 prompts and 1-512 max tokens")
    manifest = load_manifest(results_dir, spec.model_id)
    runtime = manifest.get("compat") or {}
    tp, dtype = runtime.get("tensor_parallel"), runtime.get("runtime_dtype")
    if type(tp) is not int or tp < 1 or dtype not in ("float16", "float32", "bfloat16"):
        raise ProfileError("capture manifest lacks the recorded GPU topology/dtype")
    kwargs = {"enforce_eager": True}
    if spec.model_id.startswith("google/gemma-4"):
        os.environ.setdefault("VLLM_USE_V2_MODEL_RUNNER", "1")
        os.environ.setdefault("MIA_APERTURE_GPU_BYTES", str(256 * 1024 ** 2))
        kwargs.update(limit_mm_per_prompt={"image": 0, "audio": 0, "video": 0}, max_num_seqs=8)
    actual = preflight()
    if (not actual.get("usable") or actual.get("ibm_mia_commit_actual") != IBM_MIA_COMMIT
            or len(actual.get("devices", [])) < tp):
        raise ProfileError("a prepared, pinned IBM MIA GPU runtime with the recorded GPU topology is required")
    eng = MIAEngine(spec, worker="steer", config={}, work_dir=str(Path(results_dir) / "_cfg"), runtime_dtype=dtype,
                    tensor_parallel=tp, engine_kwargs=kwargs)
    base, _ = eng.generate(prompts, steer=None, max_tokens=max_tokens)
    steered, _ = eng.generate(prompts, steer=cfg["steer"], max_tokens=max_tokens)
    return {"model_id": spec.model_id, "revision": spec.revision, "steer": cfg["steer"], "artifact": cfg["artifact"],
            "prompts": prompts, "unsteered": base, "steered": steered,
            "outputs_differ": sum(a != b for a, b in zip(base, steered)), "evidence_type": "REAL_IBM_MIA",
            "note": "Differences corroborate that steering took effect; not an attestation."}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Apply a Model Mountain steering profile on a GPU worker (IBM vLLM-Hook).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("apply")
    a.add_argument("profile", help="JSON downloaded from the Steering page")
    a.add_argument("--results", required=True, help="the Kaggle mm_results folder (emotions__<model>.json + vectors/)")
    a.add_argument("--prompt", action="append", required=True)
    a.add_argument("--allow-off-layer", action="store_true")
    r = sub.add_parser("resolve")
    r.add_argument("profile")
    r.add_argument("--results", required=True)
    args = ap.parse_args()
    doc = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    if args.cmd == "resolve":
        print(json.dumps(resolve_vector(doc.get("profile", doc), args.results), indent=2))
    else:
        print(json.dumps(apply_profile(doc, args.results, args.prompt, allow_off_layer=args.allow_off_layer), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
