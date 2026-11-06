# training-run

Lane 03 of the rlvr-lab program (`lab-rlvr-03-training-run`). Written 2026-11-06 before lanes 02
and 03 ran, by the scheduler's prediction job. Evidence ranks: **A** = this repo's committed
results or the Hub API today; **B** = a paper's own abstract as the radar logged it; **F** =
recollection.

## Prediction

**Setup assumed** (from the brief): the smallest model from lane 02, `mlx-community/Qwen2.5-Coder-0.5B-bf16`
(Hub API 200 on 2026-11-06, A), LoRA, GRPO-style group-relative updates against the visible-suite
reward, **train split only** (115 HumanEval + 264 MBPP tasks = 379, `docs/CASES.md` and the Phase
B exclusions), on the laptop (Apple M1 Pro, 16 GB, A: `sysctl` today), checkpoints every K steps,
scheduler cap 600 minutes (`queues/labs.json`, A). Evaluation at the same k = 3 and temperature
as lane 02, on the frozen held-out split (48 + 113 = 161 tasks) and on the train split.

**Baseline**: lane 02's **0.5B** rows, not Phase C's 1.5B rows. Every delta below is against the
lane-02 0.5B number on the same side with the same sampler.

**Step count**: 100–300 optimizer steps of roughly 8 prompts × 4–8 samples each, i.e. each train
task seen 2–5 times. Unsure; this is an engineering estimate for a hand-rolled MLX GRPO on a
0.5B model with 384-token completions and sandboxed scoring in the loop.

**The numbers** (point, then the range I would still call "held"; pooled = HE + MBPP, task-weighted):

| metric | train split (379 tasks) | held-out split (161 tasks) |
|---|---|---|
| Δ pass@1 visible | **+6 pp** (+3 to +15) | **+3 pp** (−1 to +7) |
| Δ pass@3 visible | +3 pp (0 to +8) | +1 pp (−3 to +5) |
| Δ pass@1 extended | +4 pp (+1 to +12) | +2 pp (−2 to +6) |
| Δ gap rate (visible-passers failing extended) | +2 pp (−3 to +8) | +2 pp (−4 to +8) |

Direction: both sides **up** on pass@1; held-out gain about **half** the train gain; pass@3 moves
less than pass@1 on both sides (sharpening, not new capability). The gap rate on held-out does
**not** rise out the top of its lane-02 CI.

**Probabilities I attach** (so the post can grade the forecast, not just the numbers):

- 0.35 — the run produces no usable curve (GRPO never stabilizes, NaN, timeout before the first
  checkpoint, or a scoring-loop bug). That is an engineering kill, posted as such, not the
  reward-hacking kill.
- 0.35 — the run completes and lands in the table above: train up, held-out up by less, kill
  clause does not fire.
- 0.30 — the kill clause fires: train pass@1 up ≥ 5 pp while held-out pass@1 stays within ±2 pp
  of baseline, with or without the gap rate rising.

Wall time 5–8 h of the 10 h cap; energy 100–250 Wh (M1 Pro package power under sustained GPU
load 20–35 W, F). The mean visible-pass reward on train batches rises from about 0.1 to about
0.2–0.3 over the run. The reward's false-positive rate measured in lane 02 (one in seven passers)
is paid at every step: the policy is rewarded for those too.

## Mechanism

GRPO with a group-relative advantage has zero gradient on tasks where every sample passes or every
sample fails; learning signal exists only on the "mixed" tasks, which in the Phase C records (A)
are about 60% of held-out tasks for the 1.5B and will be fewer for the 0.5B (lower pass@1 pushes
more tasks to 0/N). On those tasks a few hundred LoRA steps mostly re-weight completions the base
model already produces, which raises pass@1 much more than pass@k (the RLVR-sharpening result:
RL concentrates probability on already-reachable solutions and pass@k at large k barely moves or
drops; F, from memory, not in the radar). What transfers to held-out is the part of that
re-weighting that is task-independent: emitting a complete function, closing the body, returning
the right type, handling the empty input; what does not transfer is anything tied to the specific
train task, and with 379 tasks seen 2–5 times a 0.5B LoRA has little room to memorize per-task
tricks. The visible tests are not in the prompt (the HumanEval prompt is the docstring with its
examples; MBPP+'s prompt carries one example assert, F), so the classic hardcode-to-the-asserts
hack has only the docstring examples to key on, which limits how far train can run ahead of
held-out at this budget. That is why the prediction is "held-out follows train at half the size"
rather than the audit's hacking signature. The gap rate is predicted flat-to-slightly-up because
the reward pays for visible-only passers at the same rate it pays for real ones; the Phase C
finding (12.2% / 17.8%, A) says that population exists before training, and a policy that is
rewarded for it will not shrink it, but a few hundred steps on a 0.5B are too few to grow it
past a CI that is ±6 pp wide at n ≈ 100 passers. The engineering-kill probability is high because
nothing in the repo trains yet (`rlvr/` has env, sandbox, generate, metrics, mutation; no trainer,
A), `mlx_lm` is not installed in the system Python (A), and the Phase C run already needed a
tokenizer-boundary repair that a training loop must reproduce. The radar's *Audit Where Hacks
Pay* row (2610.35716, CANDIDATE narrow, B) asks for a budgeted strong-verifier audit of low-pass
groups; here the strong verifier is the extended suite and it is free, so the run should score
**every** group against both suites and log the per-step visible-only pass count, which is the
hacking curve the kill clause needs.

## Kill clause

Copied from the brief: *held-out does not move while train moves = reward hacking as the audit
predicted, posted as such.*

As written, "move" has no threshold, so the clause cannot fire or fail to fire on a number. The
operational reading this prediction commits to: **train pass@1 (pooled) up by ≥ 5 pp AND held-out
pass@1 (pooled) within ±2 pp of its lane-02 baseline at the final checkpoint**, with the per-step
visible-only-passer count reported alongside. A held-out gain of ≥ 3 pp with train ≥ 5 pp is the
"held-out follows train" outcome above and is not a kill. Reopen threshold for the post: the
held-out gap rate rising above the top of its lane-02 CI at any checkpoint.

## Sources

- `results/phase-c-2026-08-15/` per-task records — A; the mixed-task counts come from them.
- `docs/07` Phase D and kill criteria, `docs/08` "pre-registered baseline" paragraph — A.
- `docs/CASES.md` on `origin/lab-shape-rederive` — A for the split sizes and exclusions.
- `laptop-scheduler/queues/labs.json` lane 03 entry: `max_minutes` 600, GPU exclusive — A.
- Radar rows (`repo-radar/mimir/VERDICTS.md`, read-only): *Audit Where Hacks Pay* 2610.35716
  (CANDIDATE narrow, B); Guided-RLVR 2610.37041, Flat-RLVR 2610.29281, Targeted Adaptive Replay
  2610.24236, Activation-Space Exploration 2610.27012 (all PARKED, B, reopen when "the one
  training run is scheduled"; this is that run, and none of them is used in it).
- RLVR sharpening (pass@1 up, pass@k flat) — F, memory; the prediction's size ranges would widen,
  not flip, if it is wrong.
