"""Regenerate docs/RESULTS.md from saved evidence only.

    python scripts/build_results_md.py

Section 1 comes from model_mountain.defenses.run_lab() (CPU_SYNTHETIC, deterministic). Section 2 comes from
api/experiments.json (REAL_IBM_MIA, ingested from downloaded Kaggle outputs). Nothing is typed in by hand: a missing
file or a blocked phase is printed as such.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from model_mountain.defenses import run_lab  # noqa: E402


def pct(r):
    if not isinstance(r, dict) or not isinstance(r.get("rate"), (int, float)):
        return "n/a"
    ci = r.get("ci95")
    s = f"{100 * r['rate']:.0f}% (k={r.get('k')}, n={r.get('n')}"
    return s + (f", 95% CI {100 * ci[0]:.0f}–{100 * ci[1]:.0f}%)" if ci else ")")


def lab_section(lab: dict) -> list[str]:
    s = lab["scenario_suite"]
    out = ["## 1. Defense lab (CPU_SYNTHETIC)", "",
           "Source: `model_mountain.defenses.run_lab()`; also served at `/api/v1/defenses/lab`. These show what each control "
           "decides on inert fixtures. They are not attack-prevention rates for real models.", "",
           f"**Scenario suite ({s['n']} built-in cases).** Unsafe actions that would run without protection: "
           f"**{s['unprotected_unsafe_actions']}**; with Model Mountain: **{s['protected_unsafe_actions']}**. {s['note']}", "",
           "| Scenario | Category | Without protection | With Model Mountain |", "|---|---|---|---|"]
    for c in s["cases"]:
        u = "unsafe action: " + c["unprotected"]["tool"] if c["unprotected"]["unsafe_tool_would_run"] else ("released" if c["unprotected"]["released"] else "withheld")
        p = ("answered" if c["protected"]["released"] else "withheld")
        if c["protected"]["rejected_docs"]:
            p += "; quarantined " + ", ".join(c["protected"]["rejected_docs"])
        td = c["protected"].get("tool_decision")
        if td and td not in ("no_tool_requested", "read_only_policy_tool"):
            p += f"; tool denied ({td})"
        out.append(f"| {c['scenario']} | {c['category']} | {u} | {p} |")
    out += ["", "**Exfiltration guard fixtures.**", "", "| Fixture | Decision | Reasons |", "|---|---|---|"]
    for c in lab["egress"]["cases"]:
        reasons = c.get("reasons") or [r for f in c.get("findings", []) for r in f["reasons"]]
        out.append(f"| {c['case']} | {c['verdict']} | {', '.join(reasons) or '—'} |")
    m = lab["mcp_supply_chain"]
    out += ["", f"**MCP supply chain.** {m['blocked']} of {m['blocked'] + m['allowed']} fixtures blocked "
                f"({m['engine']}); allowed: " + ", ".join(c["case"] for c in m["cases"] if c["allowed"]) + "."]
    camp = lab["model_extraction"]["campaign"]
    out += ["", f"**Model extraction.** Coordinated-account fixture ({len(camp['rows'])} accounts sharing one prompt template): "
                f"per-account limits blocked {camp['per_account_limits_blocked']}, the cross-account detector blocked "
                f"{camp['campaign_detector_blocked']}; an unrelated request was still allowed: {camp['benign_unrelated_request_allowed']}.", ""]
    return out


def gpu_section(exp: dict | None) -> list[str]:
    out = ["## 2. Real-model results (REAL_IBM_MIA, Kaggle 2× Tesla T4)", ""]
    if not exp:
        return out + ["No Kaggle output has been ingested yet (`api/experiments.json` missing).", ""]
    rt = exp.get("runtime") or {}
    out += [f"Source: `api/experiments.json` (ingested {exp.get('ingested_at')}). Runtime: torch {rt.get('torch')}, "
            f"vLLM {rt.get('vllm')}, IBM MIA commit {rt.get('ibm_mia_commit')}.", ""]
    for m in exp.get("models", []):
        out += [f"### {m['model_id']} — {m['status']}", ""]
        for ph, info in (m.get("phases") or {}).items():
            if info.get("rc") and not (ph == "heads" and m.get("heads_review")):
                tail = [l.strip() for l in (info.get('error_tail') or '').splitlines()
                        if l.strip() and 'warn' not in l.lower() and 'resource_tracker' not in l]
                err = next((l for l in reversed(tail) if 'Error' in l or 'Exception' in l), tail[-1] if tail else '')
                out.append(f"- phase `{ph}` blocked (rc {info['rc']}): `{err[:300]}`")
        sh = m.get("shield")
        if sh:
            t = sh.get("test") or {}
            b0, s1 = t.get("bare") or {}, t.get("shield") or {}
            pr = s1.get("paired_vs_bare") or {}
            md, ci = pr.get("mean_diff"), pr.get("ci95")
            change = "n/a" if md is None else f"{100 * md:+.1f} points"
            if ci:
                change += f" (95% CI {100 * ci[0]:+.1f} to {100 * ci[1]:+.1f})"
            out.append(f"- **Protection steering (injection shield)**: block {(sh.get('artifact') or {}).get('block')}, strength "
                       f"{s1.get('strength')} (chosen on Tensor Trust validation). Held-out attack success {pct(b0.get('attack_success'))} -> "
                       f"{pct(s1.get('attack_success'))}; legitimate access {pct(b0.get('access_code_utility'))} -> "
                       f"{pct(s1.get('access_code_utility'))}; paired change {change}. "
                       f"Direction: {(sh.get('artifact') or {}).get('direction_source')}.")
        hd = m.get("heads")
        if hd:
            h = hd.get("heldout") or {}
            au = h.get("auroc_attack_vs_benign")
            fp32 = "; captured fp16 Q/K analyzed in FP32" if "float32" in str((hd.get("analysis") or {}).get("precision", "")) else ""
            out.append(f"- Prompt-injection detector heads: {hd['n_important_heads']} attention heads (Attention Tracker criterion, k={hd['k_used']}{fp32}); "
                       f"held-out AUROC attack vs benign {au if au is None else round(au, 3)} "
                       f"(n_attack={h.get('n_test_attack')}, n_benign={h.get('n_test_benign')}; small labeled set, exploratory). "
                       "Used only to detect injection; heads are never steered.")
        if m.get("heads_review"):
            out.append("- Attention result withheld: " + m["heads_review"]["reason"])
        if not sh:
            out.append("- **Injection shield (MIA steering)**: GPU run pending; no effect reported.")
        pr = m.get("protect")
        if pr:
            keep = ("A_bare", "B_spotlight", "D_monitor")
            out += ["", f"MIA activation monitor and prompt baseline on {pr['benchmark']} (held-out n={pr['n_test']}):", "",
                    "| Condition | Attack success | Legitimate access kept |", "|---|---|---|"]
            for name, c in pr["conditions"].items():
                if name not in keep or c.get("status") == "skipped":
                    continue
                label = c['label'] + (" (post-hoc estimate)" if c.get('estimate_type') else "")
                out.append(f"| {label} | {pct(c.get('attack_success'))} | {pct(c.get('utility'))} |")
            mon = pr.get("monitor") or {}
            out += ["", f"The MIA activation monitor (hidden-state probe trained on deepset) reaches deepset test AUROC "
                    f"{'n/a' if mon.get('auroc_deepset_test') is None else round(mon['auroc_deepset_test'], 2)}, but on Tensor Trust it flags legitimate prompts too, so it is reported as a monitor, "
                    "not a gate. Monitor-gated rows are post-hoc estimates on recorded generations.", ""]
    return out


def main() -> int:
    lab = run_lab()
    p = ROOT / "api" / "experiments.json"
    exp = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    lines = ["# Model Mountain — results", "",
             "Every number here is generated by `scripts/build_results_md.py` from saved evidence. "
             "`CPU_SYNTHETIC` and `REAL_IBM_MIA` results are kept in separate sections.", ""]
    lines += lab_section(lab) + gpu_section(exp)
    (ROOT / "docs" / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote docs/RESULTS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
