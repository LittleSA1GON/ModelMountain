"""Opt-in compatibility patches for Gemma 4 on Kaggle Tesla T4 (Turing, CC 7.5).

Patches 1-2 were found and verified on Kaggle earlier, in the private notebook
littlesa1gon/ibm-mia-gemma4-verification (Gemma-4-E2B, fp16, TP2: capture PASS, eager steering PASS).

1. vLLM 0.29.0 triton_unified_attention: Gemma's 512-wide global-attention heads need 98304 B of
   shared memory per block, but Turing has 65536 B (OutOfResources). On CC 7.5 with head_size >= 512
   only, clamp the tile sizes to 16 and use a single stage. Based on the approach discussed in vLLM PR 39018.
2. IBM MIA da42003: Gemma 4 decoder layers return (hidden_states, None). The steer worker and the hook
   installer assumed (hidden, residual), so add_vector reached nothing. Steer output[0] in that case.

Each patch checks the pinned versions, refuses if its anchor text is not found exactly once, and records
before/after SHA-256 plus a unified diff. Not applying a patch is never silent.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import subprocess
from pathlib import Path

MIA_COMMIT = "da420038fa6057c8e36c8b5457b1e02afba3cc7c"

TURING_ANCHOR = "    # Tensor descriptors for Q load / output store require every element"
TURING_MARKER = "    # MM_TURING_CLAMP"
TURING_PATCH = '''    # MM_TURING_CLAMP
    if (head_size >= 512 and q.element_size() >= 2
            and torch.cuda.get_device_capability(q.device) == (7, 5)):
        TILE_SIZE_PREFILL = min(TILE_SIZE_PREFILL, 16)
        TILE_SIZE_DECODE = min(TILE_SIZE_DECODE, 16)
        launch_num_stages = 1

'''

MIA_REPLACEMENTS = {
    "mia/workers/steer_worker.py": [
        ("""                hidden_states, residuals = output
            else:
                hidden_states = None
                residuals = output
""", """                hidden_states, residuals = output
                steer_first = residuals is None
                if steer_first:
                    residuals = hidden_states
            else:
                steer_first = False
                hidden_states = None
                residuals = output
"""),
        ("""            if is_tuple:
                return (hidden_states, residuals)
            else:
                return residuals
""", """            if is_tuple:
                # Gemma4 carries the complete stream in output[0], with output[1]=None.
                return (residuals, None) if steer_first else (hidden_states, residuals)
            else:
                return residuals
""")],
    "mia/core/hooks/install_steer.py": [
        ("""                    host.steer(out[1])
                elif isinstance(out, torch.Tensor):
""", """                    host.steer(out[1])
                elif (isinstance(out, tuple) and len(out) >= 1
                      and isinstance(out[0], torch.Tensor)):
                    host.steer(out[0])
                elif isinstance(out, torch.Tensor):
""")],
}


def _sha(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()


def _record(path: Path, before: str, after: str) -> dict:
    return {"file": str(path), "before_sha256": _sha(before), "after_sha256": _sha(after),
            "diff": "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), str(path), str(path)))[:20000]}


def patch_vllm_turing(site_vllm_dir: str) -> dict:
    path = Path(site_vllm_dir) / "v1/attention/ops/triton_unified_attention.py"
    before = path.read_text()
    if TURING_MARKER in before:
        return {"applied": False, "reason": "already patched", "file": str(path)}
    if before.count(TURING_ANCHOR) != 1:
        raise RuntimeError("vLLM attention source anchor mismatch; refusing to patch")
    after = before.replace(TURING_ANCHOR, TURING_PATCH + TURING_ANCHOR, 1)
    ast.parse(after)
    path.write_text(after)
    return {"applied": True, **_record(path, before, after)}


def patch_mia_gemma(repo: str) -> dict:
    repo_p = Path(repo)
    sha = subprocess.check_output(["git", "-C", repo, "rev-parse", "HEAD"], text=True).strip()
    if sha != MIA_COMMIT:
        raise RuntimeError("Refusing to patch a different IBM MIA revision")
    recs = []
    for rel, reps in MIA_REPLACEMENTS.items():
        path = repo_p / rel
        before = text = path.read_text()
        if "steer_first" in text or "len(out) >= 1" in text:
            recs.append({"file": rel, "applied": False, "reason": "already patched"})
            continue
        for old, new in reps:
            if text.count(old) != 1:
                raise RuntimeError(f"MIA anchor absent/ambiguous in {rel}")
            text = text.replace(old, new, 1)
        ast.parse(text)
        path.write_text(text)
        recs.append({"applied": True, **_record(path, before, text)})
    return {"commit": sha, "files": recs}


# ---------------------------------------------------------------------------------------------- 3. QK geometry
# IBM MIA da42003 reads ONE global `head_dim` for QK capture. Gemma 4 mixes sliding layers and global layers with a
# different head width, and transformers 5.17 refuses the global read ("'head_dim' is a per-layer attribute ...").
# Patch: (a) read the declared (sliding-layer) head_dim through the config's documented opt-in flag, restoring it
# afterwards; (b) capture/validate ONLY attention modules whose (num_heads, num_kv_heads, head_size) match that
# geometry and that own their K (KV-shared layers re-use another layer's cache and are skipped); every skipped
# layer is recorded on the worker as `_mm_qk_geometry` and printed. Homogeneous models (Qwen, Granite) keep every
# layer, so their behaviour is unchanged. (c) If the vLLM attention modules report one softmax scale that differs
# from the config-derived multiplier (Gemma uses QK-norm scaling), the analyzer uses the module scale; recorded.
GEOMETRY_MARKER = "MM_HETERO_GEOMETRY"

TP_SHARD_OLD = (
    '    num_h = int(getattr(text_cfg, "num_attention_heads"))\n'
    '    hidden = int(getattr(text_cfg, "hidden_size"))\n'
    '    return int(getattr(text_cfg, "head_dim", None) or hidden // num_h)\n'
)
TP_SHARD_NEW = '''    num_h = int(getattr(text_cfg, "num_attention_heads"))
    hidden = int(getattr(text_cfg, "hidden_size"))
    try:
        declared = getattr(text_cfg, "head_dim", None)
    except Exception:  # MM_HETERO_GEOMETRY: per-layer attribute guard (e.g. Gemma 4, transformers 5.x)
        flag = "allow_global_per_layer_attribute_access"
        prev = getattr(text_cfg, flag, False)
        setattr(text_cfg, flag, True)
        try:
            declared = getattr(text_cfg, "head_dim", None)
        finally:
            setattr(text_cfg, flag, prev)
    return int(declared or hidden // num_h)


def mm_filter_attn_modules(worker, matched, shard):
    """MM_HETERO_GEOMETRY: keep attention modules whose local geometry matches ``shard`` and that own their K.

    Heterogeneous models (Gemma 4: sliding vs global head width, KV-shared tail layers) would otherwise be refused
    as a whole. Skipped layers are recorded on ``worker._mm_qk_geometry``; nothing is skipped silently.
    """
    want = {"num_heads": shard.num_local_q_heads, "num_kv_heads": shard.num_local_kv_heads,
            "head_size": shard.head_dim}
    kept, skipped = [], []
    for name, module, layer_num in matched:
        got = {k: getattr(module, k, None) for k in want}
        bad = {k: (got[k], want[k]) for k in want if got[k] is not None and int(got[k]) != int(want[k])}
        shared = getattr(module, "kv_sharing_target_layer_name", None)
        if bad or shared:
            skipped.append({"layer": int(layer_num), "module": str(name),
                            "reason": "geometry" if bad else "kv_shared",
                            "mismatch": {k: [int(a), int(b)] for k, (a, b) in bad.items()},
                            "kv_sharing_target": str(shared) if shared else None})
        else:
            kept.append((name, module, layer_num))
    scales = set()
    for _, m, _ in kept:
        s = getattr(getattr(m, "impl", None), "scale", None)
        if s is None:
            s = getattr(m, "scale", None)
        if isinstance(s, (int, float)):
            scales.add(round(float(s), 9))
    conf = getattr(worker, "_conf", None)
    scale_note = None
    if isinstance(conf, dict) and len(scales) == 1:
        (sc,) = tuple(scales)
        if abs(sc - float(conf.get("attention_multiplier", sc))) > 1e-6:
            scale_note = {"config_multiplier": float(conf["attention_multiplier"]), "module_scale": sc}
            conf["attention_multiplier"] = sc
    worker._mm_qk_geometry = {"layers_captured": sorted(int(l) for _, _, l in kept),
                              "layers_skipped": skipped, "expected": want,
                              "attention_multiplier_override": scale_note}
    if isinstance(conf, dict):   # rides along in probes["config"] so the caller can report it
        conf["mm_qk_geometry"] = worker._mm_qk_geometry
    print(f"[mm/qk] captured {len(kept)} attention layers, skipped {len(skipped)} "
          f"(heterogeneous geometry or KV-shared): {[s['layer'] for s in skipped]}; "
          f"scale override: {scale_note}", flush=True)
    if not kept:
        raise RuntimeError("MM_HETERO_GEOMETRY: no attention module matches the declared head geometry")
    return kept
'''

QK_WORKER_OLD = (
    '        check_attn_modules_match_shard(list(iter_matched_modules(model, match_attn)),\n'
    '                                       self._qk_shard)\n'
    '        self._hooks = []\n'
    '        matched = []\n'
    '        for name, module, _ in iter_matched_modules(model, match_attn):\n'
)
QK_WORKER_NEW = (
    '        from mia.core.runtime.tp_shard import mm_filter_attn_modules  # MM_HETERO_GEOMETRY\n'
    '        _mm_kept = mm_filter_attn_modules(self, list(iter_matched_modules(model, match_attn)), self._qk_shard)\n'
    '        check_attn_modules_match_shard(_mm_kept, self._qk_shard)\n'
    '        self._hooks = []\n'
    '        matched = []\n'
    '        for name, module, _ in _mm_kept:\n'
)
INSTALL_OLD = (
    '    matched = list(iter_matched_modules(model, match_attn))\n'
    '    if not matched:\n'
    '        print("[graph/install] no attention modules matched ATTN_PATTERNS; "\n'
)
INSTALL_NEW = (
    '    from mia.core.runtime.tp_shard import mm_filter_attn_modules  # MM_HETERO_GEOMETRY\n'
    '    matched = mm_filter_attn_modules(worker, list(iter_matched_modules(model, match_attn)), shard)\n'
    '    if not matched:\n'
    '        print("[graph/install] no attention modules matched ATTN_PATTERNS; "\n'
)
GEOMETRY_REPLACEMENTS = {
    "mia/core/runtime/tp_shard.py": [(TP_SHARD_OLD, TP_SHARD_NEW)],
    "mia/workers/qk_capture_worker.py": [(QK_WORKER_OLD, QK_WORKER_NEW)],
    "mia/core/hooks/install.py": [(INSTALL_OLD, INSTALL_NEW)],
}


def patch_mia_qk_geometry(repo: str, dry_run: bool = False) -> dict:
    """Anchor-checked; refuses a different MIA revision or any anchor not found exactly once."""
    repo_p = Path(repo)
    sha = subprocess.check_output(["git", "-C", repo, "rev-parse", "HEAD"], text=True).strip()
    if sha != MIA_COMMIT:
        raise RuntimeError("Refusing to patch a different IBM MIA revision")
    planned, recs = [], []
    for rel, reps in GEOMETRY_REPLACEMENTS.items():
        path = repo_p / rel
        before = text = path.read_text()
        if GEOMETRY_MARKER in text:
            recs.append({"file": rel, "applied": False, "reason": "already patched"})
            continue
        for old, new in reps:
            if text.count(old) != 1:
                raise RuntimeError(f"MIA QK-geometry anchor absent/ambiguous in {rel}")
            text = text.replace(old, new, 1)
        ast.parse(text)
        planned.append((path, before, text))
    for path, before, text in planned:          # write only after every file parsed
        if not dry_run:
            path.write_text(text)
        recs.append({"applied": not dry_run, "dry_run": dry_run, **_record(path, before, text)})
    return {"commit": sha, "files": recs}


if __name__ == "__main__":
    import sys
    out, failed = {}, []
    for key, fn in (("vllm", lambda: patch_vllm_turing(str(Path(__import__("vllm").__file__).parent))),
                    ("mia", lambda: patch_mia_gemma(sys.argv[1])),
                    ("mia_qk_geometry", lambda: patch_mia_qk_geometry(sys.argv[1]))):
        try:
            out[key] = fn()
        except Exception as exc:  # recorded, never silent; the other patches still apply
            out[key] = {"applied": False, "error": f"{type(exc).__name__}: {exc}"}
            failed.append(key)
    print(json.dumps(out, indent=1))
    sys.exit(1 if failed else 0)
