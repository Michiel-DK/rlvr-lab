import argparse
import subprocess
import sys
from pathlib import Path

from . import results


def _prediction_committed(name):
    p = Path("predictions") / f"{name}.md"
    if not p.exists():
        return False, f"no predictions/{name}.md"
    text = p.read_text()
    if "## Prediction" not in text or "## Mechanism" not in text:
        return False, f"predictions/{name}.md needs '## Prediction' and '## Mechanism'"
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(p)], capture_output=True)
    if tracked.returncode != 0:
        return False, f"predictions/{name}.md is not tracked by git"
    dirty = subprocess.run(["git", "status", "--porcelain", str(p)], capture_output=True, text=True).stdout.strip()
    if dirty:
        return False, f"predictions/{name}.md has uncommitted edits"
    return True, ""


def _check_audit(a):
    from . import audit  # imports numpy via rlvr.metrics; only needed for the audit

    rep, _ = audit.run(root=a.root or audit.ROOT, page=a.page, readme=a.readme)
    print("\n".join(rep.lines))
    if rep.failures:
        print(f"\nDRIFT: {len(rep.failures)} check(s) failed", file=sys.stderr)
        return 1
    print(f"\nall {sum(1 for l in rep.lines if l.startswith('  ok'))} checks match; "
          f"{sum(1 for l in rep.lines if l.startswith('  note'))} notes (marked or not re-checkable)")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="lab")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="re-derive the posted numbers; exit 1 on drift. No paths: the published audit "
                                     "(results/ -> manifests -> SHOWCASE.md, README.md). With paths: single-file results.")
    c.add_argument("paths", nargs="*")
    c.add_argument("--root", help="repo root holding results/ and data/ (default: this checkout)")
    c.add_argument("--page", help="page to check instead of <root>/SHOWCASE.md")
    c.add_argument("--readme", help="README to check instead of <root>/README.md")
    d = sub.add_parser("diff", help="difference of two results files' headlines (b - a)")
    d.add_argument("a"); d.add_argument("b")
    r = sub.add_parser("run", help="produce a NEW results file; refuses without a committed prediction")
    r.add_argument("method"); r.add_argument("--name", required=True)
    a = p.parse_args(argv)
    if a.cmd == "check":
        if not a.paths:
            return _check_audit(a)
        rc = 0
        for path in a.paths:
            ok, msg = results.check(path)
            print(msg)
            rc = rc or (0 if ok else 1)
        return rc
    if a.cmd == "diff":
        ra, rb = results.load(a.a), results.load(a.b)
        print(f"{rb['headline'] - ra['headline']:+.6f}  ({a.b} - {a.a}, metric {ra['metric']})")
        return 0
    if a.cmd == "run":
        ok, why = _prediction_committed(a.name)
        if not ok:
            print(f"refused: {why}", file=sys.stderr)
            return 2
        print(f"run: implement the method '{a.method}' in lab/, write results/{a.name}.json with rows, metric, headline, "
              "rows_sha256, prediction_commit", file=sys.stderr)
        return 3
    return 1
