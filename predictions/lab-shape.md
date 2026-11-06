# lab-shape

Lane 01 of the rlvr-lab program (`lab-rlvr-01-refresh`). **Declared contamination**: the
scheduler ran lane 01 before this prediction job (the job depends on it, so that the
`predictions/README.md` format exists). Its PR branch `origin/lab-shape-rederive` was on the
remote when this file was written on 2026-11-06, and the prediction job read three files from it
as the brief instructs (`predictions/README.md`, `docs/CASES.md`, `LITERATURE.md`). It did **not**
read `lab/audit.py`, `lab/cli.py` beyond the prediction gate, the branch's README or SHOWCASE, or
any `lab check` output. The prediction below is therefore about the check's output, which was not
seen, not about the shape, which was.

## Prediction

`python3 -m lab check` re-derives every number in the SHOWCASE results table from the committed
`results/` files except the ones that need something not committed:

- **Re-derived** (expected): Phase B visible and extended kill rates (89.2% / 92.9%, 87.1% /
  93.5%), the pooled gaps (+3.6 / +6.4), the Phase C pass@1, pass@10 visible and extended, and
  the gap rates (12.2% / 17.8%), all from the per-mutant and per-sample JSONL; the split sha256.
- **Marked "⚠️ not re-derived"** (expected, 2–4 items): the task-mean bootstrap CIs (seeded
  resampling, re-derivable only if the bootstrap code and seed are both in the tree and the check
  reruns them); the run manifests' `git_sha` values (they point into the pre-public history, per
  `docs/CASES.md`); the per-suite Wilson CIs if the check reports points only.
- The 39-task own-repo transfer-set count re-derives from `data/e-corpus/`.

Unsure: whether the check recomputes the unbiased pass@k from the samples or reads the manifest's
stored point; only the former is a re-derivation.

## Mechanism

Every headline number in `docs/08` is a ratio of counts over the committed JSONL (mutants killed
per suite; samples passing per suite per task), and `docs/08` says the tables regenerate from the
committed scripts plus the split, so a check that recounts the JSONL recovers them exactly. What
cannot be recounted is anything that was computed with state outside the tree: a bootstrap's
random stream and git SHAs from a repository that was never published. The prediction is a list
of which numbers are which.

## Kill clause

The lane 01 brief carries no kill clause. Its stop rule is the report line: `SCHED_RESULT: OK`
only after `lab check` re-derives the posted numbers, and any number that cannot be re-derived is
marked "⚠️ not re-derived" on the page rather than dropped.
