"""Opt-in compatibility patches for Gemma 4 on Kaggle Tesla T4 (Turing, CC 7.5).

Both were found and verified on Kaggle earlier, in the private notebook
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


if __name__ == "__main__":
    import sys
    import vllm
    print(json.dumps({"vllm": patch_vllm_turing(str(Path(vllm.__file__).parent)), "mia": patch_mia_gemma(sys.argv[1])}, indent=1))
