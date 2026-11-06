# Lessons

Prediction → result, one row per run. The predictions for Phases B, C and E are the ones written in
`docs/07-rescope-verifier-adequacy.md` before those phases ran. That doc's edit history is in the
pre-public working repo, so this repo cannot show its commit date. A row whose prediction had no
number says so.

| run | prediction (where written) | result (numbers re-derived on `SHOWCASE.md` by `python3 -m lab check`) | verdict | post |
|---|---|---|---|---|
| Phase B mutation audit, 2026-08-14 | A mutation-score table exists, i.e. visible suites are thick enough to score. MBPP's ~3 asserts are "too coarse"; prefer HumanEval. Kill clause: thin suites mean no headline (docs/07) | Table exists. Gap +3.6pp HumanEval, +6.4pp MBPP; task-mean CIs exclude 0 on both | **held** (kill clause did not fire). MBPP was not too coarse to score: it showed the *larger* gap | `SHOWCASE.md`, `docs/08` |
| Phase C base-model probe, 2026-08-15 | No number. "Establishes the baseline gap" (docs/07) | 12.2% (15/123) HumanEval, 17.8% (29/163) MBPP of visible-passers fail extended | **no test**: a baseline measurement, not a prediction checked | `SHOWCASE.md`, `docs/08` |
| Phase E own-repo transfer set, 2026-08-15 | ≥30 admissible tasks, else fall back to public held-out and say so (docs/07) | 39 admissible | **held** | `data/e-corpus/README.md` |
