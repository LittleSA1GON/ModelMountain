# MIA and activation-steering agent

Scope: `model_mountain/behaviorlab.py`, `steering.py`, `mia_*_worker.py`, `steerability360_worker.py`. Confirm IBM vLLM-Hook tool API compatibility with a pinned checkout and real model architecture; validate capture tensor positions/dimensions; generate genuinely captured training/held-out activations; fit and export model/layer-specific experimental vectors; collect hook-execution evidence, A/B model outputs and latency. Steering should remain opt-in and must not replace access controls. Record unsupported runtimes as blockers, not simulated passes.
