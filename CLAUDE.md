# rlvr-lab — CLAUDE.md

One area (does a test-pass RL reward teach correct code?), one case set (`docs/CASES.md`),
predictions written down first. Read `SHOWCASE.md` and `LESSONS.md` before changing any method.

## Lab bearings

```sh
python3 -m pytest -q                      # the gate
python3 -m lab check                      # re-derives the published audit from results/; exit 1 on drift
python3 -m lab check results/<run>.json   # a lane's single-file results
python3 -m lab diff <a> <b>
python3 -m lab run <method> --name <run>  # needs a committed predictions/<run>.md; never overwrites
# internal dev harness (private): checked out locally at harness/, gitignored, not part of this tree
```

## Lab rules

- `results/` is committed evidence. A lane reads it and never regenerates it.
- A number is posted only with the command that re-derives it. A number `lab check` cannot
  re-derive carries "⚠️ not re-derived" on the page, or the check fails.
- Work in a worktree from `origin/main`; open a PR; never merge from a lane.
- What cannot be public does not go in this repo. Nothing from the archived private dev repo enters it.

---

## History (from the archived dev repo)

RLVR code-generation experiments. Early stage: `README.md` + `docs/` only — read both before
assuming any code exists.

## Bearings

Step 5 of the shared ritual in `harness/bearings.md` (read that for steps 1–4: this file →
build-flow → pin check → open state). rlvr's own first moves:

1. `git submodule status harness` — a stale pin means you're following a stale methodology.
2. Read `docs/07-rescope-verifier-adequacy.md` (the live plan) and
   `docs/08-results-verifier-adequacy.md` (the results). **Phases A–C shipped
   2026-08-14/15; the kill criterion was MET** — mutation-score gaps +3.6%/+6.4%,
   pre-RL base-model gap rate 12.2%, artifacts in `results/`. Remaining phases:
   D (train, $30–80), E (own-repo transfer, $0), G (mid-training arm, gated on
   reading PRISM — still unread). `04` and `06` remain canon context; `06`'s
   three framing corrections bind every public sentence.
3. Rollout logs produced here are a candidate emitter for the harness's shared trajectory
   schema (gated, not yet spec'd — see the harness open items before inventing a log format).
