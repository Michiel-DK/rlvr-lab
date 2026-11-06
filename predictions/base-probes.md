# base-probes

Lane 02 of the rlvr-lab program (`lab-rlvr-02-base-probes`). Written 2026-11-06 before the lane
ran, by the scheduler's prediction job, from the lane briefs, `docs/08`, the committed Phase C
samples, the lab-shape branch's `docs/CASES.md`, and the radar's `rlvr-audit` rows.

Evidence ranks used below: **A** = this repo's committed results re-read today, or the Hugging Face
Hub API queried today; **B** = a paper's own abstract as the radar logged it (claim, not depth);
**F** = recollection. Phase C numbers are the committed `results/phase-c-2026-08-15/` manifests (A).

## Prediction

**The two models** (the brief asks for names, rank A): `mlx-community/Qwen2.5-Coder-1.5B-bf16`
(the Phase C model, `DEFAULT_MODEL` in `scripts/run_phase_c_sample.py`) and
`mlx-community/Qwen2.5-Coder-0.5B-bf16`. Both answered HTTP 200 from the Hub model API on
2026-11-06 (A). The 0.5B is "the smallest model" lane 03 then trains.

**Assumed protocol**, because the numbers depend on it: temperature 0.8 and 384 max tokens as in
Phase C, k = 3 samples per task, visible suite = the reward, extended suite = the stronger proxy,
unbiased pass@k (Chen et al. 2021). If the lane picks a lower temperature, pass@1 rises and pass@3
moves toward pass@1; the gap-rate predictions stand either way.

**Baseline**: Phase C, 1.5B, held-out only, k = 10 (A). Re-estimated from the same per-sample
records at k = 3 (unbiased estimator over the committed 480 and 1,130 samples):

| metric (1.5B, held-out) | HumanEval (48 tasks) | MBPP (113 tasks) |
|---|---|---|
| pass@1 visible | 25.6% | 14.4% |
| pass@3 visible (re-estimated from Phase C) | 44.1% | 30.6% |
| pass@3 extended (re-estimated) | 39.5% | 25.6% |
| gap rate: visible-passers failing extended | 12.2% (7.5–19.1) | 17.8% (12.7–24.4) |

**Predicted table** (point, then the range I would still call "held"):

| model · side | HE pass@1 | HE pass@3 | MBPP pass@1 | MBPP pass@3 | gap rate (pooled HE+MBPP) |
|---|---|---|---|---|---|
| 1.5B · held-out | 26% (20–32) | 44% (36–52) | 14% (11–18) | 31% (25–37) | 15% (10–21) |
| 1.5B · train | 26% (20–32) | 44% (37–51) | 14% (11–18) | 31% (26–36) | 15% (11–20) |
| 0.5B · held-out | 16% (10–21) | 28% (21–36) | 9% (5–12) | 18% (13–24) | 20% (13–30) |
| 0.5B · train | 16% (11–21) | 28% (22–35) | 9% (6–12) | 18% (14–23) | 20% (14–28) |

**The gap, train vs held-out, before any training**: direction **unsure** (a coin flip), size
noise-only. Prediction: |train − held-out| pass@1 ≤ 6 pp on HumanEval and ≤ 4 pp on MBPP for
both models, and ≤ 3 pp when the two datasets are pooled (379 train vs 161 held-out tasks). A
difference outside that is a split problem to investigate, not a finding about the models.

**Model order**: 1.5B beats 0.5B on every pass@k cell, both sides, by a factor of roughly 1.5–1.8
on pass@1. The 0.5B's gap rate is **higher** than the 1.5B's (direction: up; size: unsure, the
CIs will overlap because the 0.5B produces fewer visible-passers to count).

**What it says about the reward**: the pass/fail signal GRPO would train on is wrong on roughly
one in seven of the completions it calls correct, for both models, on both sides, with the error
larger on MBPP (thinner visible suite) and larger for the weaker model. Lane 03's training reward
inherits that false-positive rate from step zero.

## Mechanism

The 1.5B rows replicate Phase C because nothing changed: same model, same sampler, same seed
family, same held-out split; k = 3 only widens the per-task sampling noise, so the pass@1 point
should land inside the Phase C CI and pass@3 near the re-estimated 44% / 31%. Train and held-out
are two halves of one seeded shuffle of task ids (`data/splits/split_v1.json`, 70/30, seed
20260814, per `docs/CASES.md` on the lab-shape branch), so before any training they are
exchangeable samples from the same task distribution; any difference is the binomial noise of 48
vs 115 and 113 vs 265 tasks, which is why the prediction is "no direction, bounded size". The
0.5B rows come from the Qwen2.5-Coder report's base-model ordering (0.5B at roughly 0.6–0.7 of
the 1.5B's HumanEval pass@1; rank F, from memory) applied to the Phase C numbers, not from the
report's absolute numbers, which were greedy and prompt-formatted differently and already sit
far above Phase C's 25.6% for the 1.5B. The gap rate rises for the weaker model because the
Phase C per-task records (A) show the passers concentrated on "mixed" tasks (29 of 48 HumanEval
tasks pass between 1 and 9 of 10; 64 of 113 MBPP), and a weaker model's visible-passing samples
on such tasks are more often partial solutions that clear a 3-to-10-assert suite by luck than
fully general ones; EvalPlus's own finding that the plus-inputs catch what the base tests miss
(`LITERATURE.md` row, held here in Phase B and C, A) is the same effect measured on the
reference-solution mutants. The pooled gap-rate point (15% for the 1.5B) is just the Phase C HE
and MBPP rates weighted by passer counts (15/123 and 29/163 = 44/286 = 15.4%, A).

## Kill clause

The lane 02 brief carries **no kill clause**. The only pre-written stop in the program for this
lane is the shared lab rule (question and prediction committed before the run; case set fixed;
deterministic grading; one command re-derives). Proposed, since the brief has none: *if the
train-vs-held-out pass@1 difference exceeds the bounds above for both models in the same
direction, stop and audit the split before lane 03 trains on it.*

## Sources

- `results/phase-c-2026-08-15/manifest-*.json`, `scores-*.jsonl` — A, re-read 2026-11-06.
- `docs/08-results-verifier-adequacy.md`, `docs/07-rescope-verifier-adequacy.md` — A (this repo).
- `docs/CASES.md`, `LITERATURE.md` on `origin/lab-shape-rederive` (lane 01's PR, open) — A for the
  split sizes; the split file itself is on `main`.
- Hub API `mlx-community/Qwen2.5-Coder-{0.5B,1.5B}-bf16` — A, HTTP 200 on 2026-11-06; nothing
  downloaded.
- Radar `rlvr-audit` rows (`repo-radar/mimir/VERDICTS.md`, read-only): *Audit Where Hacks Pay*
  (2610.35716, CANDIDATE narrow, B) — the cheap verifier is unit tests, the gamed check; this lane
  measures how gamed it already is before training.
- Qwen2.5-Coder base-model size ordering — F (memory). The prediction uses only the ratio.
