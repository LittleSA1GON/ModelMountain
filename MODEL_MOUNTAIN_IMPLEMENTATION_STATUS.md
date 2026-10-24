# Model Mountain implementation status — October 23, 2026

Returned to the original Model Mountain name. Existing security functionality retained. Additional features:

1. Verified-pins source registry + access-controlled lexical RAG.
2. Poisoned-source quarantine and retrieval audit trail.
3. Numeric mismatch and extractive citation checks; explicit abstention and review routing.
4. Optional integrated gateway grounding gate.
5. CPU reproducible reliability test cases and Streamlit demo.
6. Genuine IBM MIA capture_hs worker and contrastive steering vector fitting.
7. Genuine MIA steer/unsteered paired experiment runner, plus served API client.
8. Optional genuine MIA CoRe reranker experiment.

### What was actually executed
- 83 CPU security/reliability/mock-client tests pass.
- CPU reliability fixture runs and writes `model_mountain_results/reliability.json`.
- Existing security CLI and gateway simulation execute.

### What was NOT executed
- Real MIA hidden-state capture on a GPU.
- Real MIA CoRe analysis on a GPU.
- Real MIA activation steering on a GPU.
- Held-out attack/hallucination benchmarks establishing that steering helps.

CPU exact-match citations are a conservative release strategy, **not a general hallucination detector**. The demo registry has no production trust anchor; the CPU tests are not attack success measurements. Do not represent trained vectors as security controls without calibrated evaluation.
