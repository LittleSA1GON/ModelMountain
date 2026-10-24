"""Turn a downloaded Kaggle `mm_results/` folder into the curated `api/experiments.json` the web app shows.

    python scripts/ingest_kaggle_results.py <path/to/mm_results> [--kernel littlesa1gon/model-mountain-demo --version 3]

Only REAL_IBM_MIA phase outputs are accepted. A phase that is missing or failed shows up as `blocked`
with the exact error tail; nothing is filled in. Generated text is cut to short excerpts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = "REAL_IBM_MIA"
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


def _clip(s, n=240):
    s = str(s or "")
    return s if len(s) <= n else s[: n - 1] + "…"


def model_entry(model_id: str, res: Path, phases: list[dict]) -> dict:
    key = model_id.replace("/", "__")
    out = {"model_id": model_id, "phases": {}}
    for ph in phases:
        if ph.get("model") == model_id:
            out["phases"][ph["phase"]] = {"rc": ph.get("rc"), "seconds": ph.get("seconds"),
                                          **({"error_tail": _clip(ph.get("stderr_tail", "")[-1200:], 1200)} if ph.get("rc") else {})}
    em = _load(res / f"emotions__{key}.json")
    if em and em.get("evidence_type") == LIVE:
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
            "vectors": [{k: a[k] for k in ("concept", "block", "hidden_size", "sha256", "method")} for a in em.get("artifacts", [])],
            "capture": {k: em.get("capture", {}).get(k) for k in ("shape", "seconds", "mode")},
            "dtype_attempts": em.get("compat", {}).get("dtype_attempts"), "tensor_parallel": em.get("compat", {}).get("tensor_parallel"),
        }
    pr = _load(res / f"protect__{key}.json")
    if pr and pr.get("evidence_type") == LIVE:
        conds = {}
        for name, c in pr["conditions"].items():
            if c.get("status") == "skipped":
                conds[name] = {"label": COND_LABEL.get(name, name), "status": "skipped", "reason": c.get("reason")}
                continue
            conds[name] = {"label": COND_LABEL.get(name, name), "attack_success": _rate(c.get("attack_success")),
                           "utility": _rate(c.get("access_code_utility")), "steer_strength": c.get("steer_strength"),
                           "blocked_attacks": c.get("blocked_attacks"), "blocked_legitimate": c.get("blocked_legitimate"),
                           "paired_vs_A": c.get("paired_vs_A"),
                           "examples": [{"attack": _clip(e["attack"], 160), "reply": _clip(e["reply"], 160)} for e in c.get("examples", [])[:2]]}
        m = pr["monitor"]
        out["protect"] = {"benchmark": pr["benchmark"], "n_test": pr["n_test"], "n_validation": pr["n_validation"],
                          "chosen_calm_strength": pr["chosen_calm_strength"], "validation_sweep": pr["steer_validation_sweep"],
                          "conditions": conds, "truthfulqa": {k: {"accuracy": _rate(v["accuracy"]), "chance": v["chance"], "unparsed": v["unparsed"]}
                                                               for k, v in pr["truthfulqa_mc1"].items()},
                          "monitor": {"auroc_deepset_test": m["auroc_deepset_test"], "tpr": _rate(m["deepset_test_tpr"]),
                                      "fpr": _rate(m["deepset_test_fpr"]), "tt_attack_flagged": _rate(m["tensor_trust_attack_flag_rate"]),
                                      "tt_legit_blocked": _rate(m["tensor_trust_access_code_false_block_rate"])}}
    st = _load(res / f"steer__{key}.json")
    if st and st.get("evidence_type") == LIVE:
        b = st["baseline"]
        row = lambda r: {"attack_success": _rate(r["attack_success"]), "capability": _rate(r["capability_correct"]),
                         "sycophancy": _rate(r["sycophancy_false_claims"]), "degenerate_rate": r["degenerate_rate"]}
        out["steer"] = {"units": st["strength_units"], "baseline": row(b),
                        "rows": [{"emotion": r["emotion"], "strength": r["strength"], **row(r),
                                  "tone_shift": (r.get("tone_shift") or {}).get("mean_diff"), "tone_label": r.get("tone_label"),
                                  "outputs_changed": r.get("outputs_differ_from_baseline"),
                                  "example": _clip((r.get("examples") or {}).get("tone", [""])[0], 220)} for r in st["steered"]],
                        "baseline_example": _clip((b.get("examples") or {}).get("tone", [""])[0], 220)}
    at = _load(res / f"attn__{key}.json")
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
    models = summary.get("models") or ([summary["model"]] if summary.get("model") else [])
    fallbacks = [f for fs in (summary.get("config", {}).get("fallbacks") or {}).values() for f in fs]
    ran = {p.get("model") for p in summary.get("phases", []) if p.get("model")}
    entries = [model_entry(m, res, summary.get("phases", [])) for m in models + [f for f in fallbacks if f in ran]]
    rt = pre.get("runtime", {})
    return {
        "schema": "mm-experiments-v1", "project_id": "16f864bfa1303fc9", "evidence_type": LIVE if any(e["status"] != "blocked" for e in entries) else "NOT_CAPTURED",
        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "kernel": kernel, "kernel_version": version,
        "started": summary.get("started"), "finished": summary.get("finished"),
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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("results")
    p.add_argument("--kernel")
    p.add_argument("--version")
    p.add_argument("--out", default=str(ROOT / "api" / "experiments.json"))
    a = p.parse_args()
    res = Path(a.results)
    if not (res / "summary.json").exists():
        print("summary.json not found in", res, file=sys.stderr)
        return 2
    doc = finite(ingest(res, a.kernel, a.version))
    Path(a.out).write_text(json.dumps(doc, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    print(a.out, [(m["model_id"], m["status"]) for m in doc["models"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
