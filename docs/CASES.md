# Cases

The case set this lab grades on. Held-out is never tuned on. A new case set is a new lab.

## The audited tests

| dataset | version (EvalPlus) | tasks | visible suite = the reward | extended suite = the stronger proxy |
|---|---|---|---|---|
| HumanEval | HumanEvalPlus v0.1.10 | 164 | original HumanEval tests | base ∪ EvalPlus plus-inputs |
| MBPP | MbppPlus v0.2.0 | 378 | original MBPP asserts | base ∪ EvalPlus plus-inputs |

Loaded through `evalplus` 0.3.1 (licence Apache-2.0, read from the installed package metadata on
2026-11-06). Upstream benchmark licences:
[openai/human-eval](https://github.com/openai/human-eval) and
[google-research/mbpp](https://github.com/google-research/google-research/tree/master/mbpp) — ⚠️ not
re-checked for this page; read them there before redistributing anything.

The extended suite is **not** ground truth (docs/07, docs/06): every gap number is relative to the
strongest suite available, not to correctness.

## The split

`data/splits/split_v1.json`, schema `split-v1`, seed **20260814**, produced by
`scripts/make_split.py`: per dataset, sort the task ids, shuffle with `random.Random(seed)`, cut 70 / 30.
`tests/test_data.py` checks that the script reproduces the committed file.

| dataset | train | held-out |
|---|---|---|
| HumanEval | 115 | 49 |
| MBPP | 265 | 113 |

- **sha256** `183a619c1b688dfb42c25e6aab1066bf7611829e3e9025c046ae580f3ad4ba84`. Both Phase B manifests
  record this hash, and `python3 -m lab check` recomputes it from the committed file.
- **Commit.** In this repo's history the split enters at `c8b04b8` (2026-08-24, the first public
  snapshot) and has not changed since. It was frozen earlier, in the pre-public working history.
  The `git_sha` fields in the run manifests point into that history and cannot be resolved here.

## Which runs used which side

| run | cases | count |
|---|---|---|
| Phase B mutation audit (2026-08-14) | every task, both sides, minus the env-limited reference (`HumanEval/83`, `Mbpp/255`; see `results/phase-b-2026-08-14/README.md`) | 163 · 377 tasks |
| Phase C base-model probe (2026-08-15) | **held-out only**, minus the same env-limited tasks | 48 · 113 tasks, k=10 each |
| lane 02 base-model probes (not run) | train and held-out, reported separately | — |
| lane 03 training run (not run) | trains on **train only**; held-out is the evaluation | — |

Phase B uses reference solutions, not model output, so running it over the held-out side does not
tune anything on it. No model has been trained or tuned on any side yet.

## Own-repo transfer set (eval-only)

`data/e-corpus/`: 39 tasks mined from merged PRs of four of this account's repos. Each was reproduced
red at the base commit and green at the merge commit. They are never trained on. Titles and notes of
tasks from private repos are redacted (see `data/e-corpus/README.md`).
