# Literature

Only what this lab ran against. Each row gives the paper or repo, the claim tested, the run that
tested it, and what held. The lab's reading notes on prior art live in `docs/06-prior-art-and-positioning.md`.

| source | claim tested | run | held? |
|---|---|---|---|
| EvalPlus ([evalplus/evalplus](https://github.com/evalplus/evalplus), `evalplus` 0.3.1) | The original HumanEval/MBPP tests let wrong code pass; the plus-inputs catch some of it | Phase B (mutants of reference solutions), Phase C (Qwen2.5-Coder-1.5B samples) | **yes, here**: extended catches +3.6pp / +6.4pp more mutants, and 12.2% / 17.8% of visible-passing samples fail it |
| Chen et al. 2021, unbiased pass@k (arXiv 2107.03374, eq. 1) | used as the estimator, not tested | Phase C | n/a |
