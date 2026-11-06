"""Re-derive the published audit (Phases B, C, E) from the committed rows.

Three layers, all of which must agree or `lab check` exits 1:

1. rows -> numbers. Every headline number is recomputed from the per-mutant / per-sample JSONL
   under `results/` (and the e-corpus reports), with the same estimators the run scripts used
   (`rlvr.metrics`: Wilson, task-resampled bootstrap with the manifest's seed, unbiased pass@k).
2. numbers -> manifests. The recomputed values are compared with what each run's manifest
   recorded at run time (tolerance 1e-12; bootstrap CIs must reproduce exactly, so row order
   follows the run scripts: Phase B in file order, Phase C sorted by numeric task id).
3. numbers -> page. Each number is formatted the way the page prints it and must appear in
   SHOWCASE.md. Then every numeric token left on SHOWCASE.md must be accounted for: a derived
   number, a plan constant quoted from its source doc, or a token marked "⚠️ not re-derived".
   An unclassified number fails the check.

No API key, no GPU, no network. numpy is the only non-stdlib dependency (the bootstrap).
"""

from __future__ import annotations

import glob
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from rlvr.metrics import bootstrap_ci, pass_at_k, wilson_interval

ROOT = Path(__file__).resolve().parent.parent
TOL = 1e-12
MARK = "⚠️ not re-derived"

PHASE_B = "results/phase-b-2026-08-14"
PHASE_C = "results/phase-c-2026-08-15"
SPLIT = "data/splits/split_v1.json"
ECORPUS = "data/e-corpus"

B_VISIBLE, B_EXT_ONLY, B_SURVIVED, ENV = (
    "killed_by_visible", "killed_by_extended_only", "survived_both", "env_error")
C_FAIL, C_GAP, C_BOTH = "visible_fail", "visible_pass_extended_fail", "visible_pass_extended_pass"


# ---------------------------------------------------------------- formatting (as the page prints)
def pct(x):
    return f"{100 * x:.1f}%"


def pp(x):
    return f"{100 * x:+.1f}pp"


def signed(x):
    return f"{100 * x:+.1f}"


def num(n):
    return f"{n:,}"


def ci(lo, hi, sign=False):
    f = (lambda v: f"{100 * v:+.1f}") if sign else (lambda v: f"{100 * v:.1f}")
    return f"{f(lo)}–{f(hi)}"


# ---------------------------------------------------------------- io
def _jsonl(path):
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _json(path):
    with open(path) as fh:
        return json.load(fh)


def _task_key(task_id):  # the sort key of scripts/run_phase_c_score.py
    prefix, _, tail = task_id.partition("/")
    try:
        return (prefix, 0, int(tail))
    except ValueError:
        return (prefix, 1, tail)


@dataclass
class Report:
    lines: list = field(default_factory=list)
    failures: list = field(default_factory=list)

    def ok(self, msg):
        self.lines.append(f"  ok    {msg}")

    def fail(self, msg):
        self.lines.append(f"  FAIL  {msg}")
        self.failures.append(msg)

    def note(self, msg):
        self.lines.append(f"  note  {msg}")

    def expect(self, label, derived, recorded, tol=TOL):
        if isinstance(derived, float) or isinstance(recorded, float):
            same = recorded is not None and abs(float(derived) - float(recorded)) <= tol
        else:
            same = derived == recorded
        (self.ok if same else self.fail)(f"{label}: rows {derived!r} / manifest {recorded!r}")


# ---------------------------------------------------------------- Phase B: mutation audit
def phase_b(root, ds, rep):
    rows = _jsonl(root / PHASE_B / f"mutants-{ds}.jsonl")
    man = _json(root / PHASE_B / f"manifest-{ds}.json")
    m, cfg = man["metrics"], man["config"]

    by_task = {}  # insertion order == the script's write order (bootstrap is order-sensitive)
    for r in rows:
        by_task.setdefault(r["task_id"], []).append(r)
    cats = [r["category"] for r in rows]
    vis, ext_only, surv, env = (cats.count(c) for c in (B_VISIBLE, B_EXT_ONLY, B_SURVIVED, ENV))
    n_valid = vis + ext_only + surv
    if len(rows) != n_valid + env:
        rep.fail(f"phase B {ds}: unknown category in rows")

    gaps = []
    for trs in by_task.values():
        c = [r["category"] for r in trs]
        nv = len(c) - c.count(ENV)
        if nv:  # same float expression as the script: extended score - visible score
            kv = c.count(B_VISIBLE)
            gaps.append((kv + c.count(B_EXT_ONLY)) / nv - kv / nv)
    visible = vis / n_valid
    extended = (vis + ext_only) / n_valid
    v_ci, e_ci = wilson_interval(vis, n_valid), wilson_interval(vis + ext_only, n_valid)
    gap_point = sum(gaps) / len(gaps)
    gap_ci = bootstrap_ci(gaps, seed=cfg["seed"])

    counts = m["task_mutant_counts"]  # the full task list, incl. tasks with zero mutants
    rep.expect(f"B {ds} task_mutant_counts sum == rows", sum(counts.values()), len(rows))
    rep.expect(f"B {ds} tasks with >=1 mutant", len(by_task), sum(1 for v in counts.values() if v))
    rep.expect(f"B {ds} n_tasks", len(counts), m["n_tasks"])
    rep.expect(f"B {ds} n_mutants_total", len(rows), m["n_mutants_total"])
    rep.expect(f"B {ds} n_valid", n_valid, m["n_valid"])
    rep.expect(f"B {ds} n_env_error", env, m["n_env_error"])
    rep.expect(f"B {ds} n_survived_both", surv, m["n_survived_both"])
    sv, se = m["mutation_score_visible"], m["mutation_score_extended"]
    rep.expect(f"B {ds} visible kill", visible, sv["point"])
    rep.expect(f"B {ds} visible kill CI", list(v_ci), [sv["ci_lo"], sv["ci_hi"]])
    rep.expect(f"B {ds} extended kill", extended, se["point"])
    rep.expect(f"B {ds} extended kill CI", list(e_ci), [se["ci_lo"], se["ci_hi"]])
    rep.expect(f"B {ds} gap pooled", extended - visible, m["gap_pooled"])
    rep.expect(f"B {ds} gap task-mean", gap_point, m["gap_point"])
    rep.expect(f"B {ds} gap task-mean bootstrap CI", list(gap_ci), m["gap_ci"])
    if man.get("split_file") == SPLIT:
        sha = hashlib.sha256((root / SPLIT).read_bytes()).hexdigest()
        rep.expect(f"B {ds} split_sha256 == committed {SPLIT}", sha, man["split_sha256"])

    base_inputs = {t: trs[0]["base_n_total"] for t, trs in by_task.items() if trs[0]["base_n_total"]}
    return {
        "visible": visible, "visible_ci": v_ci, "extended": extended, "extended_ci": e_ci,
        "gap_pooled": extended - visible, "gap_point": gap_point, "gap_ci": gap_ci,
        "n_mutants": len(rows), "n_tasks": len(counts), "n_tasks_mutated": len(by_task),
        "survived_both": surv, "ext_only": ext_only, "visible_survivors": ext_only + surv,
        "visible_survive_rate": (ext_only + surv) / n_valid,
        "leak_rate": ext_only / (ext_only + surv),
        "mean_visible_inputs": sum(base_inputs.values()) / len(base_inputs),
        "excluded": cfg["excluded_tasks_env_limited"],
    }


# ---------------------------------------------------------------- Phase C: base-model probe
def phase_c(root, ds, rep, split, excluded):
    rows = _jsonl(root / PHASE_C / f"scores-{ds}-heldout-k10.jsonl")
    man = _json(root / PHASE_C / f"manifest-{ds}-heldout-k10.json")
    m, k, seed = man["metrics"], man["config"]["k"], man["config"]["seed"]

    by_task = {}
    for r in rows:
        by_task.setdefault(r["task_id"], []).append(r)
    per = []
    for tid in sorted(by_task, key=_task_key):
        c = [r["category"] for r in by_task[tid]]
        nv = len(c) - c.count(ENV)
        cv, ce = c.count(C_GAP) + c.count(C_BOTH), c.count(C_BOTH)
        ke = min(k, nv)
        per.append({"nv": nv, "ke": ke, "gap": c.count(C_GAP), "cv": cv,
                    "p1": pass_at_k(nv, cv, 1), "pkv": pass_at_k(nv, cv, ke), "pke": pass_at_k(nv, ce, ke)})

    def pooled(key, full_k=False):
        vals = [t[key] for t in per if not full_k or t["ke"] == k]
        return sum(vals) / len(vals), bootstrap_ci(vals, seed=seed)

    p1, pkv, pke = pooled("p1"), pooled("pkv", True), pooled("pke", True)
    gnum, gden = sum(t["gap"] for t in per), sum(t["cv"] for t in per)
    g_ci = wilson_interval(gnum, gden)

    expected = sorted(set(split[ds]["heldout"]) - set(excluded), key=_task_key)
    rep.expect(f"C {ds} task set == held-out minus env-limited {excluded}",
               sorted(by_task, key=_task_key), expected)
    rep.expect(f"C {ds} n_tasks", len(per), m["n_tasks"])
    rep.expect(f"C {ds} n_samples", len(rows), m["n_samples_total"])
    rep.expect(f"C {ds} samples per task == k", sorted({t['nv'] for t in per}), [k])
    for label, got, rec in (("pass@1", p1, m["pass1"]), (f"pass@{k} visible", pkv, m["pass_k_visible"]),
                            (f"pass@{k} extended", pke, m["pass_k_extended"])):
        rep.expect(f"C {ds} {label}", got[0], rec["point"])
        rep.expect(f"C {ds} {label} bootstrap CI", list(got[1]), [rec["ci_lo"], rec["ci_hi"]])
    rep.expect(f"C {ds} gap numerator", gnum, m["gap_numer"])
    rep.expect(f"C {ds} gap denominator (visible-passers)", gden, m["gap_denom"])
    rep.expect(f"C {ds} gap rate", gnum / gden, m["gap_rate"]["point"])
    rep.expect(f"C {ds} gap rate Wilson CI", list(g_ci), [m["gap_rate"]["ci_lo"], m["gap_rate"]["ci_hi"]])
    rep.note(f"C {ds}: manifest split_sha256 hashes the samples file ({man['split_file']}), "
             "which is not committed; that hash cannot be re-checked here")
    return {"k": k, "n_tasks": len(per), "n_samples": len(rows), "pass1": p1, "pass_k_visible": pkv,
            "pass_k_extended": pke, "gap_num": gnum, "gap_den": gden, "gap_rate": gnum / gden, "gap_ci": g_ci}


# ---------------------------------------------------------------- Phase E: own-repo transfer set
def phase_e(root, rep):
    reports = [_json(p) for p in sorted(glob.glob(str(root / ECORPUS / "reports" / "*.json")))]
    admissible = sum(len(r["admissible"]) for r in reports)
    rep.expect("E admissible (reports) == tasks.jsonl rows", admissible, len(_jsonl(root / ECORPUS / "tasks.jsonl")))
    return {"admissible": admissible}


# ---------------------------------------------------------------- the page
# Numbers on SHOWCASE.md that are not results: quoted from the plan, checked against their source.
PLAN_CONSTANTS = [
    ("$30–80", "docs/07-rescope-verifier-adequacy.md", "Phase D budget"),
    ("<30", "docs/07-rescope-verifier-adequacy.md", "Phase E fallback threshold"),
    ("≥30", "data/e-corpus/README.md", "Phase E bar (complement of docs/07's <30)"),
]
# Numbers on SHOWCASE.md that the committed files cannot reproduce. Each must carry MARK on the page.
NOT_REDERIVED = [
    ("~$0", "spend is not recorded in any results file"),
    ("$0", "spend is not recorded in any results file"),
    ("9.6", "HumanEval asserts/task is not in the committed results; the mutant rows give "
            "{he_inputs:.1f} visible inputs/task over the {he_mutated} mutated tasks"),
    ("~3×", "ratio built on the 9.6 above"),
]
# Stripped before tokenizing: dates, code spans, the model name, receipt heading numbers.
_STRIP = [r"`[^`]*`", r"\b\d{4}-\d{2}-\d{2}\b", r"Qwen2\.5-Coder-1\.5B", r"^#+\s*\d+\."]
_TOKEN = re.compile(r"[~+≥<]?\$?\d[\d,]*(?:\.\d+)?(?:pp|%|×)?")


def _bounded(phrase):
    tail = r"(?!\d|[.,]\d)" + ("" if phrase.endswith(("%", "pp", "×")) else r"(?!pp|%|×)")
    return re.compile(r"(?<![\w.,$~+≥<])" + re.escape(phrase) + tail)


def page_phrases(b, c, e):
    """Every derived number, formatted as SHOWCASE.md prints it."""
    he, mb, che, cmb = b["humaneval"], b["mbpp"], c["humaneval"], c["mbpp"]
    out = {}
    for ds, x in (("HumanEval", he), ("MBPP", mb)):
        out[f"B {ds} visible kill"] = [pct(x["visible"])]
        out[f"B {ds} gap pooled"] = [pp(x["gap_pooled"]), signed(x["gap_pooled"])]
        out[f"B {ds} mutants"] = [num(x["n_mutants"])]
        out[f"B {ds} tasks"] = [str(x["n_tasks"])]
        out[f"B {ds} survived both"] = [str(x["survived_both"])]
        out[f"B {ds} matched-denominator leak"] = [pct(x["leak_rate"])]
    out["B HumanEval gap pooled"].append(pct(he["gap_pooled"]))  # "mutant gap 3.6%"
    out["B HumanEval pass-visible rate"] = [pct(he["visible_survive_rate"])]
    out["B MBPP visible inputs/task"] = [f"~{mb['mean_visible_inputs']:.1f}", f"{mb['mean_visible_inputs']:.1f}"]
    out["B HumanEval visible inputs/task"] = [f"{he['mean_visible_inputs']:.1f}"]
    for ds, x in (("HumanEval", che), ("MBPP", cmb)):
        out[f"C {ds} pass@k visible"] = [pct(x["pass_k_visible"][0])]
        out[f"C {ds} gap rate"] = [pct(x["gap_rate"])]
    out["C k"] = [str(che["k"])] if che["k"] == cmb["k"] else []
    out["E admissible tasks"] = [str(e["admissible"])]
    return out


def page_pairs(b, c):
    """HumanEval/MBPP values bound to their order on SHOWCASE.md, so a swapped pair fails."""
    he, mb, che, cmb = b["humaneval"], b["mbpp"], c["humaneval"], c["mbpp"]
    return [
        f"| {pct(he['visible'])} | {pct(mb['visible'])} |",
        f"| **{pp(he['gap_pooled'])}** | **{pp(mb['gap_pooled'])}** |",
        f"| {pct(che['pass_k_visible'][0])} | {pct(cmb['pass_k_visible'][0])} |",
        f"| **{pct(che['gap_rate'])}** | **{pct(cmb['gap_rate'])}** |",
        f"{num(he['n_mutants'])} mutants / {he['n_tasks']}\ntasks on HumanEval; {num(mb['n_mutants'])} / {mb['n_tasks']} on MBPP",
        f"({he['survived_both']} / {mb['survived_both']})",
        f"({signed(mb['gap_pooled'])} vs {signed(he['gap_pooled'])} mutation gap; "
        f"{pct(cmb['gap_rate'])} vs {pct(che['gap_rate'])} model gap)",
        f"{pct(he['leak_rate'])} (HumanEval) / {pct(mb['leak_rate'])} (MBPP)",
        f"{pct(che['gap_rate'])} / {pct(cmb['gap_rate'])}",
    ]


def readme_phrases(b, c):
    """The README Results table, which carries the intervals as well."""
    out = []
    he, mb, che, cmb = b["humaneval"], b["mbpp"], c["humaneval"], c["mbpp"]

    def row(cells):  # HumanEval cell then MBPP cell, so a swapped column fails
        return "| " + " | ".join(cells) + " |"

    out = [
        f"{num(he['n_mutants'])} mutants over {he['n_tasks']} tasks, {he['n_tasks_mutated']} with at least one mutant; "
        f"{num(mb['n_mutants'])} over {mb['n_tasks']} tasks, {mb['n_tasks_mutated']} with mutants",
        f"{che['n_tasks']} tasks / {num(che['n_samples'])} samples, {cmb['n_tasks']} / {num(cmb['n_samples'])}",
        row(f"{pct(x['visible'])} ({ci(*x['visible_ci'])})" for x in (he, mb)),
        row(f"**{signed(x['gap_pooled'])} pp** (task-mean {signed(x['gap_point'])}, "
            f"CI {signed(x['gap_ci'][0])} to {signed(x['gap_ci'][1])})" for x in (he, mb)),
        row(f"{pct(x['pass_k_visible'][0])} ({ci(*x['pass_k_visible'][1])})" for x in (che, cmb)),
        row(f"**{pct(x['gap_rate'])}** ({x['gap_num']}/{x['gap_den']}, CI {ci(*x['gap_ci'])})" for x in (che, cmb)),
    ]
    return out


def check_page(text, phrases, values, rep, root, name="SHOWCASE.md"):
    body = text
    for pat in _STRIP:
        body = re.sub(pat, " ", body, flags=re.M)
    # 1. each derived number appears as printed
    for label, ps in phrases.items():
        if not ps:
            rep.fail(f"{name}: {label}: no single value to post")
        for p in ps:
            (rep.ok if _bounded(p).search(body) else rep.fail)(f"{name}: {label} = {p!r} on the page")
    # 2. classify every numeric token left
    allowed = sorted({p for ps in phrases.values() for p in ps}, key=len, reverse=True)
    for p in allowed:
        body = _bounded(p).sub(" ", body)
    for const, src, why in PLAN_CONSTANTS:
        if const in body:
            in_src = const in (root / src).read_text()
            (rep.ok if in_src else rep.fail)(f"{name}: {const!r} is a plan constant ({why}), quoted from {src}")
            body = body.replace(const, " ")
    for token, why in NOT_REDERIVED:
        pat = _bounded(token)
        for mt in list(pat.finditer(body)):
            marked = MARK in body[mt.end(): mt.end() + 160]
            (rep.note if marked else rep.fail)(
                f"{name}: {token!r} {'marked' if marked else 'NOT marked'} {MARK!r}: {why.format(**values)}")
        body = pat.sub(" ", body)
    leftover = _TOKEN.findall(body)
    if leftover:
        rep.fail(f"{name}: numbers not re-derived, not plan constants, not marked: {leftover}")
    else:
        rep.ok(f"{name}: every number on the page is derived, a quoted plan constant, or marked")


def run(root=ROOT, page=None, readme=None):
    root = Path(root)
    rep = Report()
    split = _json(root / SPLIT)["datasets"]
    b = {ds: phase_b(root, ds, rep) for ds in ("humaneval", "mbpp")}
    c = {ds: phase_c(root, ds, rep, split, b[ds]["excluded"]) for ds in ("humaneval", "mbpp")}
    e = phase_e(root, rep)
    values = {"he_inputs": b["humaneval"]["mean_visible_inputs"], "he_mutated": b["humaneval"]["n_tasks_mutated"]}
    page = Path(page) if page else root / "SHOWCASE.md"
    ptext = page.read_text()
    check_page(ptext, page_phrases(b, c, e), values, rep, root, page.name)
    for p in page_pairs(b, c):
        (rep.ok if p in ptext else rep.fail)(f"{page.name}: HumanEval/MBPP order {p!r}")
    readme = Path(readme) if readme else root / "README.md"
    rtext = readme.read_text()
    for p in readme_phrases(b, c):
        (rep.ok if p in rtext else rep.fail)(f"{readme.name} Results table: {p!r}")
    return rep, {"phase_b": b, "phase_c": c, "phase_e": e}
