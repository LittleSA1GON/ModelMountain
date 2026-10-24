"""Turn a downloaded Kaggle `mm_results/` folder into the curated `api/experiments.json` the web app shows.

    python scripts/ingest_kaggle_results.py <path/to/mm_results> [--kernel littlesa1gon/model-mountain-demo --version 3]

Only REAL_IBM_MIA phase outputs are accepted. A phase that is missing or failed shows up as `blocked`
with the exact error tail; nothing is filled in. Generated text is cut to short excerpts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
LIVE = "REAL_IBM_MIA"
PROJECT_ID = "16f864bfa1303fc9"
SECRET = re.compile(r"(?:KGAT_[A-Za-z0-9_-]{16,}|hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})")
COND_LABEL = {
    "A_bare": "No protection", "B_spotlight": "Spotlighting prompt", "C_calm_steer": "Calm steering (MIA)",
    "D_monitor": "Activation monitor (MIA)", "E_spotlight_steer": "Spotlight + steering", "F_all_layers": "All layers",
}


def _load(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _rate(r):
    if not isinstance(r, dict) or "rate" not in r:
        return None
    return {"rate": r["rate"], "k": r.get("k"), "n": r.get("n"), "ci95": r.get("ci95")}


def attack_pair(raw):
    if not raw:
        return None
    return {"n": raw.get("n"), "mean_diff": raw.get("mean_diff"), "ci95": raw.get("ci95"),
            "direction": "condition attack success minus baseline; positive is worse",
            "attacks_newly_successful": raw.get("increased", raw.get("improved")),
            "attacks_prevented": raw.get("decreased", raw.get("worse")), "ties": raw.get("ties")}


def _clip(s, n=240):
    s = SECRET.sub("[REDACTED]", str(s or ""))
    return s if len(s) <= n else s[: n - 1] + "…"


def pinned_spec(model_id):
    from model_mountain.remote_models import ModelRegistry
    registry = ROOT / "kaggle" / "model_allowlist.json"
    return ModelRegistry.from_file(str(registry)).get(model_id)


def verified_phase(res, phase, model_id, phases):
    """Reject stale, foreign, or unbound phase files before publishing their numbers."""
    record = next((p for p in phases if p.get("phase") == phase and p.get("model") == model_id), None)
    if record is None or record.get("rc") != 0:
        return None
    doc = _load(res / f"{phase}__{model_id.replace('/', '__')}.json")
    if doc is None:
        return None
    if doc.get("status") in ("not_applicable", "not_supported_on_runtime"):
        return None
    spec = pinned_spec(model_id)
    if (doc.get("project_id") != PROJECT_ID or doc.get("evidence_type") != LIVE
            or doc.get("model_id") != model_id or doc.get("revision") != spec.revision):
        raise ValueError(f"{phase}: phase provenance does not match the pinned model/project")
    return doc


def verify_vectors(em, res):
    """Check the exported direction files against the bound capture manifest."""
    spec = pinned_spec(em["model_id"])
    artifacts = em.get("artifacts") or []
    if not artifacts:
        raise ValueError("Emotion phase has no vector artifacts")
    for a in artifacts:
        if (a.get("model_id") != spec.model_id or a.get("revision") != spec.revision
                or a.get("hidden_size") != spec.hidden_size or a.get("evidence_type") != LIVE
                or type(a.get("block")) is not int or not 0 <= a["block"] < spec.num_layers):
            raise ValueError("Emotion vector model/layer binding is invalid")
        # The remote path is metadata; never follow it on the operator machine.
        filename = str(a.get("path", "")).replace("\\", "/").rsplit("/", 1)[-1]
        if not filename.endswith(".pt"):
            raise ValueError("Emotion vector artifact path is invalid")
        path = res / "vectors" / spec.model_id.replace("/", "__") / filename
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != a.get("sha256"):
            raise ValueError("Emotion vector file missing or hash mismatch")


def verify_heads(doc, res):
    path = res / "attention_heads" / (doc["model_id"].replace("/", "__") + ".json")
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != doc.get("config_sha256"):
        raise ValueError("Attention-head configuration missing or hash mismatch")
    config = _load(path) or {}
    spec = pinned_spec(doc["model_id"])
    info = config.get("model_info", {})
    if info.get("model_id") != spec.model_id or info.get("revision") != spec.revision:
        raise ValueError("Attention-head configuration model binding is invalid")
    heads = config.get("params", {}).get("important_heads", [])
    if not heads or len(heads) != doc.get("n_important_heads"):
        raise ValueError("Attention-head count is invalid")
    for head in heads:
        if (not isinstance(head, list) or len(head) != 2 or any(type(n) is not int for n in head)
                or not 0 <= head[0] < spec.num_layers or not 0 <= head[1] < spec.num_attention_heads):
            raise ValueError("Attention-head index is outside the pinned model")


HEADS_FROM: list[Path] = []      # head-only review kernels (FP32 analysis of the same capture protocol)
SHIELD_FROM: list[Path] = []     # protection-steering kernels (injection shield)


def _shield(model_id: str):
    """Injection-shield result for this model from a shield kernel, with the vector file verified by sha256."""
    for d in SHIELD_FROM:
        summ = _load(d / "summary.json") or {}
        if summ.get("project_id") not in (None, PROJECT_ID):
            continue
        doc = verified_phase(d, "shield", model_id, summ.get("phases", []))
        if doc is None:
            continue
        a = doc.get("artifact") or {}
        spec = pinned_spec(model_id)
        if (a.get("concept") != "injection_shield" or a.get("model_id") != model_id or a.get("revision") != spec.revision
                or a.get("evidence_type") != LIVE or a.get("hidden_size") != spec.hidden_size
                or type(a.get("block")) is not int or not 0 <= a["block"] < spec.num_layers):
            raise ValueError("Shield vector binding is invalid")
        name = str(a.get("path", "")).replace("\\", "/").rsplit("/", 1)[-1]
        f = d / "vectors" / model_id.replace("/", "__") / name
        if not name.endswith(".pt") or not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest() != a.get("sha256"):
            raise ValueError("Shield vector file missing or hash mismatch")
        t = doc.get("test") or {}
        sh = t.get("shield") or {}
        return {"artifact": {k: a.get(k) for k in ("concept", "block", "sha256", "hidden_size", "method", "mean_token_norm",
                                                    "direction_source", "n_hijacked_validation", "n_resisted_validation")},
                "benchmark": doc.get("benchmark"), "n_validation": doc.get("n_validation"), "n_test": doc.get("n_test"),
                "validation": doc.get("validation"),
                "test": {"bare": {"attack_success": _rate((t.get("bare") or {}).get("attack_success")),
                                  "access_code_utility": _rate((t.get("bare") or {}).get("access_code_utility"))},
                         "shield": {"attack_success": _rate(sh.get("attack_success")),
                                    "access_code_utility": _rate(sh.get("access_code_utility")), "strength": sh.get("strength"),
                                    "paired_vs_bare": sh.get("paired_vs_bare"), "utility_paired_vs_bare": sh.get("utility_paired_vs_bare"),
                                    "examples": [{k: _clip(e.get(k, ""), 160) for k in ("attack", "bare", "shield")}
                                                 for e in (sh.get("examples") or [])[:3]]}},
                "truthfulqa": doc.get("truthfulqa_mc1"),
                "source_summary_sha256": hashlib.sha256((d / "summary.json").read_bytes()).hexdigest()}
    return None


def _review_heads(model_id: str):
    """Heads from a head-only FP32 review kernel, if it ran cleanly for this model; else (None, failure-note)."""
    note = None
    for d in HEADS_FROM:
        summ = _load(d / "summary.json") or {}
        if summ.get("project_id") not in (None, PROJECT_ID):
            continue
        phases = summ.get("phases", [])
        rec = next((p for p in phases if p.get("phase") == "heads" and p.get("model") == model_id), None)
        if rec is None:
            continue
        if rec.get("rc") != 0:
            note = (rec.get("stderr_tail") or rec.get("error") or "")[-300:]
            continue
        doc = verified_phase(d, "heads", model_id, phases)
        if doc is None:
            continue
        stats = (doc.get("analysis_review") or {}).get("stats") or {}
        margin = doc.get("selection", {}).get("score_cand_max")
        if (type(margin) in (int, float) and math.isfinite(margin) and stats.get("all_raw_finite") is True
                and stats.get("all_attention_finite") is True):
            verify_heads(doc, d)
            return doc, {"precision": "captured fp16 Q/K promoted to float32 before IBM's attention analyzer",
                         "review_summary_sha256": hashlib.sha256((d / "summary.json").read_bytes()).hexdigest(),
                         "max_abs_input": stats.get("max_abs_input"), "attention_tensors": stats.get("attention_tensors")}
    return None, note


def model_entry(model_id: str, res: Path, phases: list[dict]) -> dict:
    key = model_id.replace("/", "__")
    out = {"model_id": model_id, "phases": {}}
    for ph in phases:
        if ph.get("model") == model_id:
            out["phases"][ph["phase"]] = {"rc": ph.get("rc"), "seconds": ph.get("seconds"),
                                          **({"error_tail": _clip(ph.get("stderr_tail", "")[-1200:], 1200)} if ph.get("rc") else {})}
    em = verified_phase(res, "emotions", model_id, phases)
    if em:
        verify_vectors(em, res)
        sel = em["selected"]
        out["revision"] = em.get("revision")
        out["emotions"] = {
            "selected_block": sel["block"], "depth": sel["depth"], "validation_accuracy": sel["val_accuracy"],
            "test_accuracy": em["test"]["accuracy"], "test_ci95": em["test"].get("accuracy_ci95"), "test_n": em["test"]["n"],
            "chance": em["test"]["chance"], "implicit": em.get("implicit_scenarios"), "valence_r": em.get("valence", {}).get("r_abs"),
            "valence_pc1": em.get("valence", {}).get("pc1"),
            "layer_sweep": [{k: r[k] for k in ("block", "depth", "val_accuracy", "val_accuracy_no_denoise")} for r in em["layer_sweep"]],
            "monitor_authored": em.get("monitor_auroc_attack_vs_benign"),
            "monitor_realworld": em.get("realworld_emotion_monitor_auroc"),
            "vectors": [{k: a.get(k) for k in ("concept", "block", "hidden_size", "sha256", "method")} for a in em.get("artifacts", [])],
            "mean_token_norm_train": sel.get("mean_token_norm_train"),
            "metric_note": em.get("metric_note"),
            "capture": {k: em.get("capture", {}).get(k) for k in ("shape", "seconds", "mode")},
            "dtype_attempts": em.get("compat", {}).get("dtype_attempts"), "tensor_parallel": em.get("compat", {}).get("tensor_parallel"),
        }
    pr = verified_phase(res, "protect", model_id, phases)
    if pr:
        conds = {}
        for name, c in pr["conditions"].items():
            if c.get("status") == "skipped":
                conds[name] = {"label": COND_LABEL.get(name, name), "status": "skipped", "reason": c.get("reason")}
                continue
            conds[name] = {"label": COND_LABEL.get(name, name), "attack_success": _rate(c.get("attack_success")),
                           "utility": _rate(c.get("access_code_utility")), "steer_strength": c.get("steer_strength"),
                           "blocked_attacks": c.get("blocked_attacks"), "blocked_legitimate": c.get("blocked_legitimate"),
                           "paired_vs_A": attack_pair(c.get("paired_vs_A")), "estimate_type": c.get("estimate_type"),
                           "examples": [{"attack": _clip(e["attack"], 160), "reply": _clip(e["reply"], 160)} for e in c.get("examples", [])[:2]]}
        m = pr["monitor"]
        out["protect"] = {"benchmark": pr["benchmark"], "n_test": pr["n_test"], "n_validation": pr["n_validation"],
                          "chosen_calm_strength": pr["chosen_calm_strength"], "validation_sweep": pr["steer_validation_sweep"],
                          "conditions": conds, "truthfulqa": {k: {"accuracy": _rate(v["accuracy"]), "chance": v["chance"], "unparsed": v["unparsed"]}
                                                               for k, v in pr["truthfulqa_mc1"].items()},
                          "monitor": {"auroc_deepset_test": m["auroc_deepset_test"], "tpr": _rate(m["deepset_test_tpr"]),
                                      "fpr": _rate(m["deepset_test_fpr"]), "tt_attack_flagged": _rate(m["tensor_trust_attack_flag_rate"]),
                                      "tt_legit_blocked": _rate(m["tensor_trust_access_code_false_block_rate"])}}
    st = verified_phase(res, "steer", model_id, phases)
    if st:
        b = st["baseline"]
        row = lambda r: {"attack_success": _rate(r["attack_success"]), "capability": _rate(r["capability_correct"]),
                         "sycophancy": _rate(r["sycophancy_false_claims"]),
                         "degenerate_rate": r.get("degenerate_rate_open_ended", r.get("degenerate_rate"))}
        out["steer"] = {"units": st["strength_units"], "baseline": row(b),
                        "rows": [{"emotion": r["emotion"], "strength": r["strength"], **row(r),
                                  "tone_shift": (r.get("tone_shift") or {}).get("mean_diff"), "tone_label": r.get("tone_label"),
                                  "hook_evidence": r.get("hook_evidence"),
                                  "example": _clip((r.get("examples") or {}).get("tone", [""])[0], 220)} for r in st["steered"]],
                        "baseline_example": _clip((b.get("examples") or {}).get("tone", [""])[0], 220)}
    review, review_note = _review_heads(model_id)
    hd = verified_phase(res, "heads", model_id, phases)
    analysis = {"precision": (hd or {}).get("analysis_precision", {}).get("analysis_dtype", "as captured")} if hd else None
    if review is not None:
        hd, analysis = review, review_note
    elif hd:
        verify_heads(hd, res)
    rec = next((p for p in phases if p.get("phase") == "heads" and p.get("model") == model_id), None)
    if hd is None and rec is not None:
        raw = _load(res / f"heads__{key}.json") or {}
        out["heads_review"] = {"status": raw.get("status") or ("failed_on_runtime" if rec.get("rc") else "missing"),
                               "reason": raw.get("reason") or "IBM MIA Q/K capture did not complete for this model on Kaggle T4 "
                               "(Gemma 4 mixes per-layer attention geometries); no heads are reported."}
    if hd:
        margin = hd.get("selection", {}).get("score_cand_max")
        if type(margin) not in (int, float) or not math.isfinite(margin):
            out["heads_review"] = {"status": "withheld", "reason": "Non-finite attention selection diagnostic; requires a stable capture/analysis rerun."}
        else:
            out["heads"] = {"role": "prompt_injection_detector", "analysis": analysis, "n_important_heads": hd["n_important_heads"], "k_used": hd["selection"]["k_used"],
                            "k_paper_default": hd["selection"].get("k_paper_default"), "capped": hd["selection"].get("capped"),
                            "top": hd.get("important_heads_top20"), "config_sha256": hd.get("config_sha256"),
                            "heldout": hd.get("heldout_detection"), "head_capture_coverage": hd.get("head_capture_coverage")}
    shield = _shield(model_id)
    if shield:
        out["shield"] = shield
    at = verified_phase(res, "attn", model_id, phases)
    if at:
        out["attn"] = {"status": at.get("status", "measured"), "auroc": at.get("auroc_attack_vs_benign"), "reason": at.get("reason")}
    ok = "emotions" in out
    out["status"] = "measured" if ok and "protect" in out else "partial" if ok else "blocked"
    return out


def ingest(res: Path, kernel: str | None = None, version: str | None = None) -> dict:
    summary = _load(res / "summary.json") or {}
    pre = _load(res / "preflight.json") or {}
    stories = _load(res / "stories.json") or {}
    manifest = _load(res / "realworld_manifest.json") or {}
    source = _load(res / "source_run.json") or {}
    if source:
        if (source.get("project_id") != PROJECT_ID or source.get("provenance_type") != "OPERATOR_RECORD"
                or source.get("summary_sha256") != hashlib.sha256((res / "summary.json").read_bytes()).hexdigest()
                or not re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9_-]+", source.get("kernel_ref", ""))):
            raise ValueError("Operator run provenance does not bind this summary")
        kernel, version = source["kernel_ref"], source.get("kernel_version")
    if summary.get("project_id") != PROJECT_ID or pre.get("project_id") != PROJECT_ID:
        raise ValueError("Summary or preflight belongs to another project")
    if stories:
        gen = stories.get("generator") or {}
        generator = pinned_spec(gen.get("model_id"))
        spec_sha = hashlib.sha256((ROOT / "examples/emotion_vectors/stories_spec.json").read_bytes()).hexdigest()
        if (stories.get("project_id") != PROJECT_ID or stories.get("evidence_type") != "REAL_MODEL_GENERATION"
                or gen.get("revision") != generator.revision or stories.get("spec_sha256") != spec_sha):
            raise ValueError("Generated story corpus provenance is invalid")
    models = summary.get("models") or ([summary["model"]] if summary.get("model") else [])
    if summary.get("kind") == "stories":          # generator kernel: provenance only, no target model
        models = []
    fallbacks = [f for fs in (summary.get("config", {}).get("fallbacks") or {}).values() for f in fs]
    ran = {p.get("model") for p in summary.get("phases", []) if p.get("model")}
    entries = [model_entry(m, res, summary.get("phases", [])) for m in models + [f for f in fallbacks if f in ran]]
    rt = pre.get("runtime", {})
    if any(e["status"] != "blocked" for e in entries):
        from model_mountain.mia_runtime import IBM_MIA_COMMIT
        if rt.get("ibm_mia_commit_actual") != IBM_MIA_COMMIT:
            raise ValueError("Real-model results require the pinned IBM MIA runtime")
    return {
        "schema": "mm-experiments-v1", "project_id": "16f864bfa1303fc9", "evidence_type": LIVE if any(e["status"] != "blocked" for e in entries) else "NOT_CAPTURED",
        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "kernel": kernel, "kernel_version": version,
        "started": summary.get("started"), "finished": summary.get("finished"),
        "source_artifacts": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in res.glob("*.json")
                             if p.name != "source_run.json"},
        "source_record": source or None,
        "runtime": {"gpus": rt.get("devices"), "torch": rt.get("torch"), "vllm": rt.get("vllm_version"),
                    "ibm_mia_commit": rt.get("ibm_mia_commit_actual"), "driver": (rt.get("cuda_driver_banner") or [None])[0]},
        "preflight_usable": summary.get("preflight_usable"), "preflight_blockers": summary.get("preflight_blockers"),
        "gemma_patches": {"rc": (pre.get("install_steps", {}).get("gemma_t4_patches") or {}).get("rc")},
        "stories": {"generator": stories.get("generator"), "kept": stories.get("kept"),
                    "dropped": stories.get("dropped_for_emotion_words_or_length"), "seconds": stories.get("seconds"),
                    "sha256": hashlib.sha256((res / "stories.json").read_bytes()).hexdigest() if (res / "stories.json").exists() else None,
                    "samples": [{"emotion": s["emotion"], "text": _clip(s["text"], 320)} for s in
                                {s["emotion"]: s for s in (stories.get("stories") or []) if s["split"] == "test"}.values()][:11]},
        "realworld": manifest.get("manifest"), "realworld_n": manifest.get("n"),
        "models": entries,
    }


def finite(v):
    """JSON for browsers: NaN/inf become null."""
    import math
    if isinstance(v, float):
        return v if math.isfinite(v) else None
    if isinstance(v, dict):
        return {k: finite(x) for k, x in v.items()}
    if isinstance(v, list):
        return [finite(x) for x in v]
    return v


def merge(docs: list[dict]) -> dict:
    """Combine per-model kernel ingests (one Kaggle kernel per model) into one experiments document."""
    base = dict(next((d for d in docs if d["models"]), docs[0]))
    story = next((d["stories"] for d in docs if (d.get("stories") or {}).get("kept")), None)
    if story:
        base["stories"] = story
    base["models"] = [m for d in docs for m in d["models"]]
    base["kernels"] = [{"kernel": d.get("kernel"), "started": d.get("started"), "finished": d.get("finished"),
                        "version": d.get("kernel_version"), "preflight_usable": d.get("preflight_usable"),
                        "source_artifacts": d.get("source_artifacts"), "source_record": d.get("source_record")} for d in docs]
    base["evidence_type"] = LIVE if any(m["status"] != "blocked" for m in base["models"]) else "NOT_CAPTURED"
    return base


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("results", nargs="+", help="one or more mm_results folders (one per model kernel)")
    p.add_argument("--kernel")
    p.add_argument("--version")
    p.add_argument("--out", default=str(ROOT / "api" / "experiments.json"))
    p.add_argument("--shield-from", action="append", default=[],
                   help="protection-steering (injection shield) mm_results folder")
    p.add_argument("--heads-from", action="append", default=[],
                   help="head-only review mm_results folder (FP32 analysis); preferred for heads when it ran cleanly")
    a = p.parse_args()
    HEADS_FROM[:] = [Path(h) for h in a.heads_from]
    SHIELD_FROM[:] = [Path(h) for h in a.shield_from]
    docs = []
    for r in a.results:
        res = Path(r)
        if not (res / "summary.json").exists():
            print("summary.json not found in", res, file=sys.stderr)
            return 2
        docs.append(ingest(res, a.kernel, a.version))
    doc = finite(merge(docs))
    Path(a.out).write_text(json.dumps(doc, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    print(a.out, [(m["model_id"], m["status"]) for m in doc["models"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
