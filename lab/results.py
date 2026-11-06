import hashlib
import json


def load(path):
    with open(path) as fh:
        return json.load(fh)


def derive(rows, metric):
    """The posted number: mean of `metric` over `rows`. Replace with the lab's own derivation; keep it deterministic."""
    vals = [float(r[metric]) for r in rows]
    if not vals:
        raise ValueError("no rows")
    return sum(vals) / len(vals)


def digest(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check(path):
    """Re-derive the headline from the rows and compare with what the file posts. Returns (ok, message)."""
    d = load(path)
    rows, metric = d["rows"], d["metric"]
    got = derive(rows, metric)
    posted = float(d["headline"])
    if d.get("rows_sha256") and d["rows_sha256"] != digest(rows):
        return False, f"{path}: rows_sha256 does not match the rows"
    if abs(got - posted) > 1e-9:
        return False, f"{path}: posted headline {posted} but rows derive {got}"
    return True, f"{path}: {metric} = {got:.6f} over {len(rows)} rows, matches"
