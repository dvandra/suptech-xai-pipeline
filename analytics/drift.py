"""Model & data drift monitoring via the Population Stability Index (PSI).

PSI is the standard metric supervisors and model-risk teams use to decide when
a deployed model needs re-checking. Rule-of-thumb interpretation:

    PSI < 0.10  -> no significant shift
    0.10-0.25   -> moderate shift, investigate
    PSI > 0.25  -> major shift, model/data review required

This module compares a *reference* population against a *current* population.
When only one dataset is available (the demo case) it splits the classified
records by reporting period into an earlier reference half and a later current
half, so drift can be demonstrated end-to-end. It also exposes a generic
`compare()` for two real batches.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


def _psi_from_counts(ref: Counter, cur: Counter, keys: list) -> tuple[float, list[dict]]:
    ref_total = sum(ref.values()) or 1
    cur_total = sum(cur.values()) or 1
    eps = 1e-6
    psi = 0.0
    breakdown = []
    for k in keys:
        r = ref.get(k, 0) / ref_total
        c = cur.get(k, 0) / cur_total
        r_adj, c_adj = max(r, eps), max(c, eps)
        contrib = (c_adj - r_adj) * math.log(c_adj / r_adj)
        psi += contrib
        breakdown.append(
            {"bucket": str(k), "ref_pct": round(r, 4), "cur_pct": round(c, 4),
             "contribution": round(contrib, 4)}
        )
    return psi, breakdown


def _band(psi: float) -> str:
    if psi < 0.10:
        return "stable"
    if psi < 0.25:
        return "moderate"
    return "major"


def _categorical_psi(ref_vals: list, cur_vals: list) -> dict:
    ref, cur = Counter(ref_vals), Counter(cur_vals)
    keys = sorted(set(ref) | set(cur))
    psi, breakdown = _psi_from_counts(ref, cur, keys)
    return {"psi": round(psi, 4), "band": _band(psi), "breakdown": breakdown}


def _numeric_psi(ref_vals: list[float], cur_vals: list[float], bins: int = 10) -> dict:
    if not ref_vals or not cur_vals:
        return {"psi": None, "band": "n/a", "breakdown": []}
    lo, hi = min(ref_vals + cur_vals), max(ref_vals + cur_vals)
    if hi == lo:
        return {"psi": 0.0, "band": "stable", "breakdown": []}
    width = (hi - lo) / bins

    def bucketize(v: float) -> int:
        return min(int((v - lo) / width), bins - 1)

    ref = Counter(bucketize(v) for v in ref_vals)
    cur = Counter(bucketize(v) for v in cur_vals)
    psi, breakdown = _psi_from_counts(ref, cur, list(range(bins)))
    return {"psi": round(psi, 4), "band": _band(psi), "breakdown": breakdown}


def compare(reference: list[dict], current: list[dict]) -> dict:
    """PSI between two batches of classified records."""
    return {
        "reference_n": len(reference),
        "current_n": len(current),
        "predicted_category_psi": _categorical_psi(
            [r["predicted_category"] for r in reference],
            [r["predicted_category"] for r in current],
        ),
        "anomaly_score_psi": _numeric_psi(
            [r["anomaly_score"] for r in reference],
            [r["anomaly_score"] for r in current],
        ),
    }


def compute() -> dict:
    """Demo drift: split the single classified dataset by reporting period."""
    if not config.CLASSIFIED_JSONL.exists():
        raise FileNotFoundError(
            f"{config.CLASSIFIED_JSONL} not found - run the pipeline first."
        )
    rows = []
    with config.CLASSIFIED_JSONL.open() as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))

    rows.sort(key=lambda r: r["time_period"])
    mid = len(rows) // 2
    reference, current = rows[:mid], rows[mid:]
    result = compare(reference, current)
    result["note"] = (
        "Reference = earlier reporting periods, Current = later periods. "
        "Use compare() with two real batches in production."
    )
    return result


if __name__ == "__main__":
    print(json.dumps(compute(), indent=2, default=str))
