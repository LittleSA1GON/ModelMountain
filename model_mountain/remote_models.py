"""Remote / Kaggle model registry, download planning and compatibility checks.

Scope (MM-REMOTE-MODELS): decide *whether* a Hugging Face model can be pulled and run
under IBM vLLM-Hook (package ``mia``) on a given GPU runtime, and *which* MIA use cases
are genuinely available for it. Pure Python; no network, torch or vLLM import at module
load. Network metadata is injected so tests and the Vercel API stay offline.

Nothing here claims a model ran. Runtime evidence is produced only by
``model_mountain.mia_runtime`` on a real GPU.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
import fnmatch
import json
import math
import re

# Pinned upstream. Verified 2026-10-23 from github.com/IBM/vLLM-Hook (main).
IBM_MIA_REPO = "https://github.com/IBM/vLLM-Hook.git"
IBM_MIA_COMMIT = "da420038fa6057c8e36c8b5457b1e02afba3cc7c"
IBM_MIA_REQUIREMENTS = {
    "vllm": "0.29.0", "torch": "2.13.0", "transformers": "5.17.0",
    "triton": "3.7.1", "safetensors": "0.8.0", "numpy": "2.3.5", "zstandard": "0.25.0",
}
# vLLM 0.29 / CUDA 13 wheels: Turing (sm75) is the oldest supported architecture.
MIN_COMPUTE_CAPABILITY = (7, 5)
BF16_COMPUTE_CAPABILITY = (8, 0)

USE_CASES = ("capture_hs", "steer", "attention_tracker", "core_reranker",
             "hnode_hallucination", "tool_call_risk", "attnlink")
# Use cases that need a model-specific trained artifact shipped by IBM (heads/probe).
ARTIFACT_BOUND = {"attention_tracker", "core_reranker", "hnode_hallucination",
                  "tool_call_risk", "attnlink"}

# Upstream config files present at IBM_MIA_COMMIT (model_configs/<use_case>/<file>.json).
# Generic use cases (capture_hs, steer) work on any architecture whose decoder layers MIA
# can locate; artifact-bound ones are ONLY available where IBM shipped the artifact.
UPSTREAM_CONFIGS = {
    "Qwen/Qwen2-1.5B-Instruct": {"steer": "activation_steer/Qwen2-1.5B-Instruct.json",
                                  "attention_tracker": "attention_tracker/Qwen2-1.5B-Instruct.json",
                                  "capture_hs": "hidden_states/Qwen2-1.5B-Instruct.json"},
    "Qwen/Qwen2.5-1.5B-Instruct": {"hnode_hallucination": "hnode_hallucination/Qwen2.5-1.5B-Instruct.infer.json"},
    "Qwen/Qwen2.5-3B-Instruct": {"capture_hs": "hidden_states/Qwen2.5-3B-Instruct.json",
                                  "hnode_hallucination": "hnode_hallucination/Qwen2.5-3B-Instruct.infer.json"},
    "Qwen/Qwen2.5-7B-Instruct": {"tool_call_risk": "tool_call_risk/Qwen2.5-7B-Instruct.infer.json"},
    "Qwen/Qwen2.5-Coder-7B-Instruct": {"attnlink": "attnlink/Qwen2.5-Coder-7B-Instruct.json"},
    "microsoft/Phi-3-mini-4k-instruct": {"steer": "activation_steer/Phi-3-mini-4k-instruct.json"},
    "ibm-granite/granite-3.1-8b-instruct": {"steer": "activation_steer/granite-3.1-8b-instruct.json",
                                             "attention_tracker": "attention_tracker/granite-3.1-8b-instruct.json",
                                             "capture_hs": "hidden_states/granite-3.1-8b-instruct.json"},
    "RedHatAI/granite-3.1-2b-instruct-quantized.w4a16": {
        "steer": "activation_steer/granite-3.1-2b-instruct-quantized.w4a16.json",
        "attention_tracker": "attention_tracker/granite-3.1-2b-instruct-quantized.w4a16.json",
        "core_reranker": "core_reranker/granite-3.1-2b-instruct-quantized.w4a16.json"},
    "meta-llama/Llama-3.1-8B-Instruct": {"capture_hs": "hidden_states/Llama-3.1-8B-Instruct.json"},
    "meta-llama/Meta-Llama-3-8B-Instruct": {"attention_tracker": "attention_tracker/Meta-Llama-3-8B-Instruct.json"},
    "mistralai/Mistral-7B-Instruct-v0.3": {"attention_tracker": "attention_tracker/Mistral-7B-Instruct-v0.3.json",
                                            "core_reranker": "core_reranker/Mistral-7B-Instruct-v0.3.json"},
}

# Architectures whose vLLM implementation names decoder blocks in a form MIA matches
# (model.layers.N / transformer.h.N / model.decoder.layers.N / language_model.model.layers.N).
MIA_LAYER_ARCHITECTURES = {
    "Qwen2ForCausalLM", "Qwen3ForCausalLM", "LlamaForCausalLM", "MistralForCausalLM",
    "Phi3ForCausalLM", "GraniteForCausalLM", "Gemma2ForCausalLM", "Gemma3ForCausalLM",
    "GPT2LMHeadModel", "OPTForCausalLM",
}
# Architectures vLLM serves but MIA has not been validated on: allowed as EXPERIMENTAL (warning, not
# blocker) because the live run fails closed on missing hook evidence ("no decoder layers matched").
EXPERIMENTAL_ARCHITECTURES = {
    "Gemma4ForConditionalGeneration", "Gemma4ForCausalLM", "Gemma3ForConditionalGeneration",
    "GraniteMoeHybridForCausalLM", "GraniteMoeForCausalLM",
}
GATED_PREFIXES = ("meta-llama/", "mistralai/")

_MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")
_REVISION = re.compile(r"^[0-9a-f]{40}$")
DEFAULT_ALLOW_PATTERNS = ("*.safetensors", "*.json", "tokenizer*", "*.model", "*.tiktoken", "*.txt")
DENY_PATTERNS = ("*.bin", "*.pt", "*.pth", "*.pkl", "*.ckpt", "*.py", "*.sh", "*.exe", "*.so")
DTYPE_BYTES = {"float16": 2, "bfloat16": 2, "float32": 4, "w4a16": 0.5, "w8a16": 1}


class ModelPolicyError(ValueError):
    """A model, revision or runtime request is refused (never silently adjusted)."""


@dataclass(frozen=True)
class GPUSpec:
    name: str
    vram_gib: float
    compute_capability: tuple[int, int]
    count: int = 1
    driver_cuda: str | None = None      # e.g. "13.0" from nvidia-smi; None = unknown

    def supports_bf16(self) -> bool:
        return tuple(self.compute_capability) >= BF16_COMPUTE_CAPABILITY


# Kaggle accelerators as of 2026-10 (verify on the live runtime; preflight records actuals).
KAGGLE_GPUS = {
    "T4x2": GPUSpec("Tesla T4", 15.0, (7, 5), count=2),
    "P100": GPUSpec("Tesla P100-PCIE-16GB", 16.0, (6, 0), count=1),
}


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    revision: str                         # 40-char commit SHA; branch names refused
    architecture: str
    params_billion: float
    hidden_size: int
    num_layers: int
    num_attention_heads: int
    max_position_embeddings: int
    dtype: str = "bfloat16"               # checkpoint dtype or quant scheme
    license: str = "unknown"
    gated: bool = False
    trust_remote_code: bool = False
    notes: str = ""

    def __post_init__(self):
        validate_model_id(self.model_id)
        if not _REVISION.match(self.revision):
            raise ModelPolicyError("Pin an exact 40-character commit SHA, not a branch or tag")
        if self.trust_remote_code:
            raise ModelPolicyError("trust_remote_code models are refused by default policy")
        if self.params_billion <= 0 or self.hidden_size <= 0 or self.num_layers <= 0:
            raise ModelPolicyError("Model dimensions must be positive")
        if self.dtype not in DTYPE_BYTES:
            raise ModelPolicyError(f"Unsupported checkpoint dtype {self.dtype!r}")


def validate_model_id(model_id: str) -> str:
    if not isinstance(model_id, str) or not _MODEL_ID.match(model_id) or ".." in model_id:
        raise ModelPolicyError("Model id must be 'owner/name' using safe characters")
    return model_id


def spec_from_hf_config(model_id: str, revision: str, config: dict, *, params_billion: float,
                        license: str = "unknown", gated: bool | None = None,
                        quantization: str | None = None) -> ModelSpec:
    """Build a spec from a downloaded/fetched ``config.json`` (trusted only after pinning)."""
    tc = config.get("text_config", config)
    archs = config.get("architectures") or []
    if len(archs) != 1:
        raise ModelPolicyError("config.json must declare exactly one architecture")
    if config.get("auto_map"):
        raise ModelPolicyError("Model requires custom code (auto_map); refused without review")
    dtype = quantization or str(tc.get("torch_dtype") or tc.get("dtype") or config.get("torch_dtype")
                                or config.get("dtype") or "bfloat16")
    try:
        return ModelSpec(
            model_id=model_id, revision=revision, architecture=archs[0],
            params_billion=float(params_billion), hidden_size=int(tc["hidden_size"]),
            num_layers=int(tc["num_hidden_layers"]), num_attention_heads=int(tc["num_attention_heads"]),
            max_position_embeddings=int(tc.get("max_position_embeddings", 2048)), dtype=dtype,
            license=license, gated=model_id.startswith(GATED_PREFIXES) if gated is None else gated)
    except KeyError as exc:
        raise ModelPolicyError(f"config.json missing required field {exc}") from exc


def estimate_vram_gib(spec: ModelSpec, *, max_model_len: int, runtime_dtype: str,
                      batch_tokens: int | None = None, mia_buffer_gib: float = 4.0) -> dict:
    """Conservative serving estimate: weights + KV cache + activations + MIA capture buffer.

    IBM docs (main, 2026-10) reserve a 4 GiB capture aperture outside vLLM's
    gpu_memory_utilization; it can be lowered via MIA_APERTURE_GPU_BYTES.
    """
    wbytes = DTYPE_BYTES["float16" if runtime_dtype in ("float16", "bfloat16") and spec.dtype not in ("w4a16", "w8a16") else spec.dtype]
    weights = spec.params_billion * 1e9 * wbytes / 2**30
    head_dim = spec.hidden_size / spec.num_attention_heads
    # Assume GQA-unknown worst case = MHA. 2 (K,V) * layers * hidden * 2 bytes per token.
    kv_per_token = 2 * spec.num_layers * spec.num_attention_heads * head_dim * 2
    tokens = batch_tokens or max_model_len
    kv = kv_per_token * tokens / 2**30
    overhead = 1.0 + 0.10 * weights
    total = weights + kv + overhead + mia_buffer_gib
    return {"weights_gib": round(weights, 2), "kv_cache_gib": round(kv, 2),
            "overhead_gib": round(overhead, 2), "mia_buffer_gib": mia_buffer_gib,
            "total_gib": round(total, 2)}


def compatibility(spec: ModelSpec, gpu: GPUSpec, *, max_model_len: int = 2048,
                  tensor_parallel: int = 1, mia_buffer_gib: float = 4.0) -> dict:
    """Return an explicit verdict. Blockers make ``compatible`` False; never auto-downgrade."""
    blockers, warnings = [], []
    if tuple(gpu.compute_capability) < MIN_COMPUTE_CAPABILITY:
        blockers.append(f"{gpu.name} sm{gpu.compute_capability[0]}{gpu.compute_capability[1]} is below "
                        f"vLLM 0.29/CUDA 13 minimum sm{MIN_COMPUTE_CAPABILITY[0]}{MIN_COMPUTE_CAPABILITY[1]}")
    if gpu.driver_cuda is not None:
        try:
            if float(gpu.driver_cuda) < 13.0:
                blockers.append(f"Driver supports CUDA {gpu.driver_cuda}; torch 2.13 cu13 wheels need >= 13.0")
        except ValueError:
            warnings.append("Unparseable driver CUDA version; preflight must verify")
    else:
        warnings.append("Driver CUDA version unknown until on-runtime preflight")
    runtime_dtype = "bfloat16" if gpu.supports_bf16() else "float16"
    if spec.dtype == "bfloat16" and runtime_dtype == "float16":
        warnings.append("bf16 checkpoint will run as fp16 on this GPU; overflow is possible and must be checked")
    if spec.architecture in EXPERIMENTAL_ARCHITECTURES:
        warnings.append(f"Architecture {spec.architecture} is EXPERIMENTAL for MIA: hook evidence is required at runtime")
    elif spec.architecture not in MIA_LAYER_ARCHITECTURES:
        blockers.append(f"Architecture {spec.architecture} not in MIA decoder-layer naming allowlist; "
                        "verify 'no decoder layers matched' does not occur before enabling")
    if spec.model_id.startswith("google/gemma") and runtime_dtype == "float16":
        warnings.append("Gemma checkpoints are bf16-trained; fp16 on T4 may overflow (runtime checks for non-finite/degenerate output)")
    if max_model_len > spec.max_position_embeddings:
        blockers.append("Requested context exceeds model max_position_embeddings")
    if tensor_parallel < 1 or tensor_parallel > gpu.count or spec.num_attention_heads % tensor_parallel:
        blockers.append("Invalid tensor_parallel for GPU count / head count")
    est = estimate_vram_gib(spec, max_model_len=max_model_len, runtime_dtype=runtime_dtype,
                            mia_buffer_gib=mia_buffer_gib)
    per_gpu_need = (est["total_gib"] - mia_buffer_gib) / tensor_parallel + mia_buffer_gib
    if per_gpu_need > gpu.vram_gib * 0.95:
        blockers.append(f"Estimated {per_gpu_need:.1f} GiB per GPU exceeds {gpu.vram_gib} GiB")
    if spec.gated:
        warnings.append("Gated model: requires HF token via Kaggle Secret HF_TOKEN and accepted license")
    return {"model_id": spec.model_id, "revision": spec.revision, "gpu": gpu.name,
            "runtime_dtype": runtime_dtype, "max_model_len": max_model_len,
            "tensor_parallel": tensor_parallel, "estimate": est,
            "per_gpu_gib": round(per_gpu_need, 2), "compatible": not blockers,
            "blockers": blockers, "warnings": warnings, "evidence_type": "STATIC_ESTIMATE"}


def capability_matrix(spec: ModelSpec, *, local_artifacts: dict | None = None) -> dict:
    """Per-use-case availability. Artifact-bound cases need an upstream or reviewed local artifact."""
    upstream = UPSTREAM_CONFIGS.get(spec.model_id, {})
    local = (local_artifacts or {}).get(spec.model_id, {})
    layered = spec.architecture in MIA_LAYER_ARCHITECTURES or spec.architecture in EXPERIMENTAL_ARCHITECTURES
    out = {}
    for case in USE_CASES:
        if case in ("capture_hs", "steer"):
            ok = layered
            source = upstream.get(case) or local.get(case) or ("generated" if ok else None)
            reason = None if ok else "decoder layers not locatable by MIA"
        else:
            source = upstream.get(case) or local.get(case)
            ok = layered and source is not None
            reason = None if ok else "requires model-specific heads/probe artifact not available for this model"
        out[case] = {"available": ok, "config_source": source, "reason": reason}
    return out


@dataclass(frozen=True)
class DownloadPlan:
    model_id: str
    revision: str
    allow_patterns: tuple[str, ...]
    files: tuple[str, ...]
    total_bytes: int
    requires_token: bool
    trust_remote_code: bool = False
    rejected_files: tuple[str, ...] = field(default=())

    def snapshot_kwargs(self, cache_dir: str) -> dict:
        """Arguments for ``huggingface_hub.snapshot_download`` (token read from env, never here)."""
        return {"repo_id": self.model_id, "revision": self.revision, "cache_dir": cache_dir,
                "allow_patterns": list(self.allow_patterns)}


def plan_download(model_id: str, revision: str, siblings: list[dict], *, gated: bool = False,
                  max_total_gib: float = 20.0,
                  allow_patterns: tuple[str, ...] = DEFAULT_ALLOW_PATTERNS) -> DownloadPlan:
    """Choose files from HF ``siblings`` metadata ({'rfilename','size'}). Refuses pickle-only repos."""
    validate_model_id(model_id)
    if not _REVISION.match(revision):
        raise ModelPolicyError("Download requires a pinned 40-character commit SHA")
    chosen, rejected, total = [], [], 0
    for s in siblings:
        name = s.get("rfilename", "")
        if not name or name.startswith("/") or ".." in name.split("/"):
            raise ModelPolicyError(f"Unsafe repository path {name!r}")
        if any(fnmatch.fnmatch(name.split("/")[-1], p) for p in DENY_PATTERNS):
            rejected.append(name)
            continue
        if any(fnmatch.fnmatch(name.split("/")[-1], p) for p in allow_patterns):
            chosen.append(name)
            total += int(s.get("size") or 0)
    if not any(n.endswith(".safetensors") for n in chosen):
        raise ModelPolicyError("No safetensors weights; pickle checkpoints are refused")
    if "config.json" not in [n.split("/")[-1] for n in chosen]:
        raise ModelPolicyError("Repository has no config.json")
    if total > max_total_gib * 2**30:
        raise ModelPolicyError(f"Download {total / 2**30:.1f} GiB exceeds limit {max_total_gib} GiB")
    return DownloadPlan(model_id, revision, tuple(allow_patterns), tuple(sorted(chosen)), total,
                        requires_token=gated, rejected_files=tuple(sorted(rejected)))


class ModelRegistry:
    """Allowlist of pinned models. Additions go through ``register`` with a reviewed spec."""

    def __init__(self, specs: list[ModelSpec] | None = None):
        self._specs: dict[str, ModelSpec] = {}
        for s in specs or []:
            self.register(s)

    def register(self, spec: ModelSpec) -> ModelSpec:
        if spec.model_id in self._specs and self._specs[spec.model_id].revision != spec.revision:
            raise ModelPolicyError("Model already registered at a different revision; unregister first")
        self._specs[spec.model_id] = spec
        return spec

    def get(self, model_id: str) -> ModelSpec:
        try:
            return self._specs[validate_model_id(model_id)]
        except KeyError:
            raise ModelPolicyError(f"{model_id} is not on the allowlist") from None

    def items(self) -> list[ModelSpec]:
        return [self._specs[k] for k in sorted(self._specs)]

    def matrix(self, gpu: GPUSpec, *, max_model_len: int = 2048) -> list[dict]:
        rows = []
        for spec in self.items():
            row = compatibility(spec, gpu, max_model_len=max_model_len,
                                tensor_parallel=min(gpu.count, 2) if spec.params_billion > 4 and gpu.count > 1 else 1)
            row["capabilities"] = capability_matrix(spec)
            row["license"], row["gated"] = spec.license, spec.gated
            rows.append(row)
        return rows

    def to_json(self) -> str:
        return json.dumps([asdict(s) for s in self.items()], indent=2)

    @classmethod
    def from_file(cls, path: str) -> "ModelRegistry":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls([ModelSpec(**{**d}) for d in data])


def default_registry_path() -> str:
    import os
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "kaggle", "model_allowlist.json")


def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Model Mountain remote model compatibility matrix (static)")
    p.add_argument("--registry", default=default_registry_path())
    p.add_argument("--gpu", choices=sorted(KAGGLE_GPUS), default="T4x2")
    p.add_argument("--max-model-len", type=int, default=2048)
    p.add_argument("--output")
    a = p.parse_args(argv)
    rows = ModelRegistry.from_file(a.registry).matrix(KAGGLE_GPUS[a.gpu], max_model_len=a.max_model_len)
    text = json.dumps({"gpu": asdict(KAGGLE_GPUS[a.gpu]), "ibm_mia_commit": IBM_MIA_COMMIT,
                       "evidence_type": "STATIC_ESTIMATE", "models": rows}, indent=2)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
