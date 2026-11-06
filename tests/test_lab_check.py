"""The gate on `lab check`: it passes on the committed tree and fails on any drift."""

import json
import shutil
from pathlib import Path

import pytest

from lab import audit, results
from lab.cli import main

ROOT = audit.ROOT


def test_committed_tree_rederives():
    rep, values = audit.run()
    assert rep.failures == []
    assert main(["check"]) == 0
    he = values["phase_c"]["humaneval"]
    assert (he["gap_num"], he["gap_den"]) == (15, 123)


@pytest.mark.parametrize("edit", [
    lambda s: s.replace("12.2%", "12.3%", 1),          # a posted number drifts from the rows
    lambda s: s + "\nAlso 42% faster.\n",             # a new number nobody re-derives
    lambda s: s.replace("(⚠️ not re-derived: a plan budget", "(a plan budget", 1),  # a mark removed
])
def test_page_drift_fails(tmp_path, edit):
    page = tmp_path / "SHOWCASE.md"
    page.write_text(edit((ROOT / "SHOWCASE.md").read_text()))
    assert main(["check", "--page", str(page)]) == 1


def test_row_drift_fails(tmp_path):
    for d in ("results", "data", "docs"):
        shutil.copytree(ROOT / d, tmp_path / d)
    for f in ("SHOWCASE.md", "README.md"):
        shutil.copy(ROOT / f, tmp_path / f)
    assert main(["check", "--root", str(tmp_path)]) == 0
    p = tmp_path / audit.PHASE_B / "mutants-humaneval.jsonl"
    rows = [json.loads(l) for l in p.read_text().splitlines()]
    i = next(i for i, r in enumerate(rows) if r["category"] == "killed_by_visible")
    rows[i]["category"] = "survived_both"
    p.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    rep, _ = audit.run(root=tmp_path)
    assert any("visible kill" in f for f in rep.failures)
    assert main(["check", "--root", str(tmp_path)]) == 1


def test_single_file_results_check(tmp_path):
    rows = [{"case": "c1", "score": 0.25}, {"case": "c2", "score": 0.75}]
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"metric": "score", "headline": 0.5, "rows_sha256": results.digest(rows), "rows": rows}))
    assert main(["check", str(p)]) == 0
    p.write_text(json.dumps({"metric": "score", "headline": 0.6, "rows": rows}))
    assert main(["check", str(p)]) == 1


def test_run_refuses_without_prediction():
    assert main(["run", "m", "--name", "no-such-run"]) == 2
