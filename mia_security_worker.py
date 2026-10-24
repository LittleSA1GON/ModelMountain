"""Run REAL IBM MIA Attention Tracker on a single supported Qwen2-1.5B model.

Run as a fresh subprocess using the isolated venv from the supplied benchmark.
This script never substitutes fake MIA scores. Unsupported models fail closed.
Requires the repo's genuine attention_tracker/Qwen2-1.5B-Instruct.json config.
"""
import argparse
import json
import math
import multiprocessing as mp
import os
import re
import time
from pathlib import Path

MODEL = "Qwen/Qwen2-1.5B-Instruct"


def tool_parse(output):
    """Treat unvalidated model text as text. Only structured tool suggestions count."""
    m = re.search(r"\{.*\}", output, flags=re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                tool = obj.get("tool", "")
                args = obj.get("tool_args", {})
                return (str(obj.get("answer", output)), tool if isinstance(tool, str) else "",
                        args if isinstance(args, dict) else {})
        except (ValueError, TypeError):
            pass
    return output, "", {}


def main():
    from mia import MiaLLM
    from vllm import SamplingParams
    from model_mountain.real_inputs import make_inputs
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-cases", type=int, default=0)
    args = ap.parse_args()
    cfg = Path(args.repo) / "model_configs/attention_tracker/Qwen2-1.5B-Instruct.json"
    if not cfg.is_file():
        raise FileNotFoundError("IBM Qwen2-1.5B Attention Tracker config not found: " + str(cfg))
    config = json.loads(cfg.read_text())
    if not config.get("params", {}).get("important_heads"):
        raise ValueError("IBM config missing actual calibrated heads")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print("Loading verified attention configuration", cfg, flush=True)
    llm = MiaLLM(model=MODEL, worker_name="capture_qk", analyzer_name="attn_tracker",
                 config_file=str(cfg), hook_dir=str(output_path.parent / "mia_probes"),
                 dtype="float16", enforce_eager=True, max_model_len=1024, max_num_seqs=1,
                 max_num_batched_tokens=1024, gpu_memory_utilization=0.50)
    cases = make_inputs()
    if args.max_cases:
        cases = cases[:args.max_cases]
    evidence = {}
    for idx, case in enumerate(cases):
        t0 = time.perf_counter()
        instruction, data = case["instruction"], case["data"]
        messages = [{"role": "system", "content": instruction},
                    {"role": "user", "content": "Data: " + data}]
        tok = llm.tokenizer
        # This is the explicit Qwen2-1.5B token-span recipe in IBM's demo.
        # Do not silently extrapolate it to Qwen2.5, SmolLM, or Granite.
        input_range = ((3, 3 + len(tok.encode(instruction))),
                       (-5 - len(tok.encode(data)), -5))
        prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        if len(tok.encode(prompt)) > 960:
            raise ValueError("Prompt longer than available max context; avoid truncating span recipe")
        outputs = llm.generate(prompt, SamplingParams(max_tokens=48, temperature=0.0, seed=42),
                               use_tqdm=False)
        if not outputs or not outputs[0].outputs or not outputs[0].probes:
            raise RuntimeError("MIA returned empty generation or empty Q/K probe: " + case["key"])
        analyzed = llm.analyze(analyzer_spec={"input_range": input_range, "attn_func": "sum_normalize"},
                               probes=outputs[0].probes)
        values = analyzed.get("score")
        if not isinstance(values, (list, tuple)) or not values:
            raise RuntimeError("No MIA Attention Tracker score for " + case["key"])
        score = float(values[0])
        if not math.isfinite(score):
            raise RuntimeError("Non-finite MIA score")
        generated = outputs[0].outputs[0].text
        answer, tool, tool_args = tool_parse(generated)
        evidence[case["key"]] = {
            "text": answer, "raw_generation": generated, "proposed_tool": tool,
            "tool_args": tool_args, "mia_score": score,
            "mia_score_origin": "IBM_MIA_attn_tracker_Qwen2_1_5B",
            "engine": "REAL_IBM_MIA_vllm", "duration_s": round(time.perf_counter()-t0, 3),
            "output_tokens": len(outputs[0].outputs[0].token_ids),
            "input_range": input_range,
        }
        output_path.write_text(json.dumps({"status": "PARTIAL", "model": MODEL, "results": evidence}, indent=2))
        print("MIA", idx + 1, "/", len(cases), case["key"], "score", round(score, 5), flush=True)
    output_path.write_text(json.dumps({"status": "PASS", "model": MODEL,
                                       "analyzer": "attn_tracker", "results": evidence}, indent=2))
    print("REAL_MIA_PASS", len(evidence), "cases", flush=True)


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
