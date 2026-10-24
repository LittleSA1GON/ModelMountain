"""Build private Kaggle GPU script kernels for the Model Mountain v2 emotion-vector study.

    python kaggle/build_kernel.py --owner USER --stories                       # 1) generator kernel -> stories.json
    python kaggle/build_kernel.py --owner USER --model Qwen/Qwen2.5-1.5B-Instruct # 2) one kernel per target model
    python kaggle/build_kernel.py --owner USER --preflight-only                 # GPU/driver probe, no installs

Model kernels attach the stories kernel output through kernel_sources (USER/model-mountain-stories).
Each output directory is new: model_mountain_results/kaggle_bundle/<slug>-<UTC>/{run.py,kernel-metadata.json,BUNDLE_MANIFEST.json}.
The bundle embeds only reviewed source + datasets; anything that looks like a credential aborts the build.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from model_mountain.remote_models import ModelRegistry  # noqa: E402

FILES = [
    "model_mountain/__init__.py", "model_mountain/remote_models.py", "model_mountain/mia_runtime.py",
    "examples/emotion_vectors/stories_spec.json", "examples/emotion_vectors/behavior_tests.json",
    "examples/emotion_vectors/contrast_implicit.json", "examples/emotion_vectors/MANIFEST.json",
    "kaggle/model_allowlist.json", "kaggle/t4_gemma_patches.py",
]
SECRET_RE = re.compile(r"(KGAT_[0-9a-f]{16,}|hf_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9_-]{20,}|BEGIN [A-Z ]*PRIVATE KEY)")
STORIES_SLUG = "model-mountain-stories"
DEFAULT_GENERATOR = "Qwen/Qwen2.5-7B-Instruct"
# Gemma 4 has no bf16 on T4: try fp16 first, fall back to fp32 (memory permitting) and record both attempts.
DTYPE_OVERRIDES = {"google/": ["float16"]}   # fp32 does not fit E4B on 2x15 GB; fp16 verified for E2B
# Settings that passed in littlesa1gon/ibm-mia-gemma4-verification: text-only, eager (graph steering unverified).
ENGINE_KWARGS = {"google/gemma-4": {"limit_mm_per_prompt": {"image": 0, "audio": 0, "video": 0}, "enforce_eager": True,
                                    "max_num_seqs": 8}}
ENV = {"google/gemma-4": {"VLLM_USE_V2_MODEL_RUNNER": "1", "MIA_APERTURE_GPU_BYTES": str(256 * 1024 ** 2)}}


def model_slug(model_id: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", model_id.lower()).strip("-")
    return ("mm-" + s)[:50].rstrip("-")


def _bundle() -> tuple[bytes, dict]:
    buf, manifest = io.BytesIO(), {}
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in FILES:
            data = (ROOT / rel).read_bytes()
            if SECRET_RE.search(data.decode("utf-8", "replace")):
                raise SystemExit(f"Refusing to bundle {rel}: looks like it contains a credential")
            z.writestr(rel, data)
            manifest[rel] = hashlib.sha256(data).hexdigest()
    return buf.getvalue(), manifest


def kernel_config(*, kind: str, model: str | None = None, generator: str = DEFAULT_GENERATOR,
                  preflight_only: bool = False, extra: dict | None = None) -> dict:
    spec_sha = hashlib.sha256((ROOT / "examples/emotion_vectors/stories_spec.json").read_bytes()).hexdigest()
    cfg = {"kind": kind, "max_model_len": 2048, "gpu_memory_utilization": 0.70, "install": not preflight_only,
           "preflight_only": preflight_only, "spec_sha256": spec_sha, "phase_timeout": 10800}
    if kind == "stories":
        cfg["generator_model"] = generator
    else:
        cfg.update(model=model, layer_fractions=[0.25, 0.4, 0.5, 0.6, 0.67, 0.8], story_start_token=50,
                   steer_emotions=["desperate", "calm", "happy", "angry", "afraid"], strengths=[-0.2, -0.1, 0.1, 0.2],
                   tone_classifier="j-hartmann/emotion-english-distilroberta-base", run_attn=True)
        for prefix, dts in DTYPE_OVERRIDES.items():
            if model.startswith(prefix):
                cfg["dtypes"] = dts
        for prefix, kw in ENGINE_KWARGS.items():
            if model.startswith(prefix):
                cfg["engine_kwargs"] = kw
        for prefix, env in ENV.items():
            if model.startswith(prefix):
                cfg["env"] = env
    cfg.update(extra or {})
    return cfg


DEMO_MODELS = ["Qwen/Qwen2.5-1.5B-Instruct", "ibm-granite/granite-3.1-2b-instruct", "google/gemma-4-E4B-it"]
DEMO_FALLBACKS = {"google/gemma-4-E4B-it": ["google/gemma-4-E2B-it"]}


def demo_config(models=None, generator: str = DEFAULT_GENERATOR) -> dict:
    """One kernel: stories, then each model in turn (minimum demo set), per-model overrides kept separately."""
    models = models or DEMO_MODELS
    cfg = kernel_config(kind="model", model=models[0])
    cfg.update(kind="demo", generator_model=generator, models=models, fallbacks=DEMO_FALLBACKS, per_model={})
    for m in models + [f for fs in DEMO_FALLBACKS.values() for f in fs]:
        mc = kernel_config(kind="model", model=m)
        cfg["per_model"][m] = {k: mc[k] for k in ("dtypes", "engine_kwargs", "env") if k in mc}
    for k in ("dtypes", "engine_kwargs", "env", "model"):
        cfg.pop(k, None)
    return cfg


def write_notebook(run_py: Path, out: Path) -> Path:
    """Kaggle web 'Import notebook' form: cell 1 writes the self-contained script, cell 2 runs it."""
    src = run_py.read_text(encoding="utf-8")
    cells = [
        {"cell_type": "markdown", "metadata": {}, "source": ["# Model Mountain - IBM vLLM-Hook (MIA) emotion-vector study\n",
                 "Accelerator: GPU T4 x2, Internet: on. Outputs: /kaggle/working/mm_results/"]},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
         "source": ["%%writefile /kaggle/mm_run.py\n" + src]},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
         "source": ["!python /kaggle/mm_run.py 2>&1 | tail -n 400"]},
    ]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
          "language_info": {"name": "python"}, "kaggle": {"accelerator": "nvidiaTeslaT4", "isInternetEnabled": True,
          "isGpuEnabled": True, "language": "python", "sourceType": "notebook"}}, "nbformat": 4, "nbformat_minor": 5}
    path = out / "model_mountain_demo.ipynb"
    path.write_text(json.dumps(nb), encoding="utf-8")
    return path


def build(owner: str, config: dict, *, slug: str, out_root: Path | None = None, kernel_sources: list[str] | None = None) -> Path:
    allow = ROOT / "kaggle" / "model_allowlist.json"
    if not allow.exists():
        raise SystemExit("kaggle/model_allowlist.json missing: run kaggle/resolve_revisions.py first")
    reg = ModelRegistry.from_file(str(allow))
    for key in ("model", "generator_model"):
        if config.get(key):
            reg.get(config[key])  # refuse non-allowlisted / unpinned models
    for m in list(config.get("models") or []) + [f for fs in (config.get("fallbacks") or {}).values() for f in fs]:
        reg.get(m)
    blob, manifest = _bundle()
    src = (ROOT / "kaggle" / "run_mia_kaggle.py").read_text(encoding="utf-8")
    run = src.replace('"__BUNDLE__"', '"' + base64.b64encode(blob).decode() + '"', 1)
    run = run.replace("__CONFIG__", json.dumps(config), 1)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = (out_root or ROOT / "model_mountain_results" / "kaggle_bundle") / f"{slug}-{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    (out / "run.py").write_text(run, encoding="utf-8", newline="\n")
    title = {"stories": "Model Mountain stories", "demo": "Model Mountain demo"}.get(config["kind"], f"MM {config.get('model', 'preflight')}")[:50]
    meta = {"id": f"{owner}/{slug}", "title": title, "code_file": "run.py", "language": "python", "kernel_type": "script",
            "is_private": True, "enable_gpu": True, "enable_internet": True, "dataset_sources": [],
            "competition_sources": [], "kernel_sources": kernel_sources or [], "model_sources": []}
    (out / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    (out / "BUNDLE_MANIFEST.json").write_text(json.dumps({"files": manifest, "config": config, "kernel_id": meta["id"],
                                                          "run_py_sha256": hashlib.sha256(run.encode()).hexdigest()},
                                                         indent=2) + "\n", encoding="utf-8")
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--owner", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--stories", action="store_true", help="build the story-generator kernel")
    g.add_argument("--model", help="build one target-model kernel")
    g.add_argument("--preflight-only", action="store_true")
    g.add_argument("--demo", action="store_true", help="one kernel: stories + minimum demo model set")
    p.add_argument("--generator", default=DEFAULT_GENERATOR)
    p.add_argument("--no-attn", action="store_true")
    a = p.parse_args()
    if a.demo:
        out = build(a.owner, demo_config(generator=a.generator), slug="model-mountain-demo")
        write_notebook(out / "run.py", out)
    elif a.stories:
        out = build(a.owner, kernel_config(kind="stories", generator=a.generator), slug=STORIES_SLUG)
    elif a.preflight_only:
        out = build(a.owner, kernel_config(kind="model", model="Qwen/Qwen2.5-1.5B-Instruct", preflight_only=True),
                    slug="model-mountain-preflight")
    else:
        out = build(a.owner, kernel_config(kind="model", model=a.model, extra={"run_attn": not a.no_attn}),
                    slug=model_slug(a.model), kernel_sources=[f"{a.owner}/{STORIES_SLUG}"])
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
