# Kaggle GPU runbook (for MM-GPU-VALIDATION)

## Credential handling (human-provisioned)

- The human has placed a Kaggle API token in `~/.kaggle/access_token` (`%USERPROFILE%\.kaggle\access_token` on Windows). The Kaggle CLI reads it automatically.
- Agents **never** read, print, copy, log or commit the token. Don't put it in notebooks, `.ai/`, artifacts, messages or env dumps. To check auth, run `kaggle kernels list --mine --page-size 1` and record only the success or failure.
- If auth fails, send a `BLOCKER` to `human`. Do not retry with any other credential.

## Run

1. `pip install -U kaggle` (needs a CLI version that supports `access_token`), then run `kaggle --version`.
2. Generate the notebook from canonical source (MM-CPU-INTEGRATION). Write `kernel-metadata.json` with `"enable_gpu": true`, `"enable_internet": true` and `"is_private": true`.
3. `kaggle kernels push -p <kernel dir>`, poll `kaggle kernels status <user>/<slug>`, then `kaggle kernels output <user>/<slug> -p model_mountain_results/kaggle/`.
4. Record the GPU type, CUDA/driver, vLLM and IBM vLLM-Hook commit, model checkpoint, dtype, layer, tensor dims, seed, hook logs, latency and VRAM, as required by MM-GPU-VALIDATION.
5. If Kaggle's T4/P100 and CUDA can't run the pinned vLLM-Hook, record the exact error as a compatibility blocker. Never substitute CPU or synthetic output.
