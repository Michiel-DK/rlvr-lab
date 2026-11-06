# rlvr-codegen — CLAUDE.md

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
