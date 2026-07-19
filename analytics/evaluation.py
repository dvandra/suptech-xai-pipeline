"""AI testing & evaluation harness.

Evaluates two things:

1. The anomaly *detector* (the embedding + nearest-centroid model), using the
   ground-truth labels the data generator injects. Because we know which
   records were seeded as outliers, we can compute honest precision / recall /
   F1 and sweep the decision threshold to find its optimum.

2. The LLM *explanations* (the Chain-of-Thought XAI output):
     * output validity  - does every response yield a parseable risk rating?
     * faithfulness      - do explanations actually cite the red-flag terms
                           present in the record they describe?
     * LLM-as-judge      - a local model (or deterministic fallback) rates each
                           explanation 1-5 against a rubric.

All metrics are computed deterministically where possible so the suite can run
in CI as a regression gate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from data_generator.kafka_producer import ANOMALOUS_PURPOSES  # noqa: E402

_TRUE_ANOMALY_SET = {p.lower() for p in ANOMALOUS_PURPOSES}


# --------------------------------------------------------------------------- #
# Detector evaluation
# --------------------------------------------------------------------------- #
def _load_classified() -> list[dict]:
    if not config.CLASSIFIED_JSONL.exists():
        raise FileNotFoundError(
            f"{config.CLASSIFIED_JSONL} not found - run the pipeline first."
        )
    rows = []
    with config.CLASSIFIED_JSONL.open() as fh:
        for line in fh:
            r = json.loads(line)
            r["_truth"] = r["txn_purpose"].strip().lower() in _TRUE_ANOMALY_SET
            rows.append(r)
    return rows


def _prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def detection_metrics(rows: list[dict] | None = None) -> dict:
    rows = rows or _load_classified()
    tp = sum(1 for r in rows if r["_truth"] and r["is_anomaly"])
    fp = sum(1 for r in rows if not r["_truth"] and r["is_anomaly"])
    fn = sum(1 for r in rows if r["_truth"] and not r["is_anomaly"])
    tn = sum(1 for r in rows if not r["_truth"] and not r["is_anomaly"])
    metrics = _prf(tp, fp, fn)
    metrics.update(
        {
            "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
            "accuracy": round((tp + tn) / len(rows), 4) if rows else 0.0,
            "support_anomalies": tp + fn,
            "n": len(rows),
        }
    )
    return metrics


def threshold_sweep(rows: list[dict] | None = None, steps: int = 25) -> dict:
    """Sweep the score threshold to find the F1-optimal operating point."""
    rows = rows or _load_classified()
    scores = [r["anomaly_score"] for r in rows]
    truth = [r["_truth"] for r in rows]
    if not scores:
        return {}
    mu = sum(scores) / len(scores)
    var = sum((s - mu) ** 2 for s in scores) / len(scores)
    std = var ** 0.5
    lo, hi = min(scores), max(scores)

    curve, best = [], None
    for i in range(steps + 1):
        thr = lo + (hi - lo) * i / steps
        tp = sum(1 for s, t in zip(scores, truth) if t and s > thr)
        fp = sum(1 for s, t in zip(scores, truth) if not t and s > thr)
        fn = sum(1 for s, t in zip(scores, truth) if t and s <= thr)
        prf = _prf(tp, fp, fn)
        sigma = (thr - mu) / std if std else 0.0
        point = {"threshold": round(thr, 4), "sigma": round(sigma, 3), **prf}
        curve.append(point)
        if best is None or prf["f1"] > best["f1"]:
            best = point

    return {
        "score_mean": round(mu, 4),
        "score_std": round(std, 4),
        "current_sigma": config.ANOMALY_SIGMA,
        "best_operating_point": best,
        "curve": curve,
    }


# --------------------------------------------------------------------------- #
# LLM explanation evaluation
# --------------------------------------------------------------------------- #
def _load_explanations() -> list[dict]:
    if not config.EXPLANATIONS_JSONL.exists():
        raise FileNotFoundError(
            f"{config.EXPLANATIONS_JSONL} not found - run stage 4 first."
        )
    with config.EXPLANATIONS_JSONL.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _present_red_flags(text: str) -> list[str]:
    t = text.lower()
    return [term for term in config.RED_FLAG_TERMS if term in t]


def llm_output_metrics(explanations: list[dict] | None = None) -> dict:
    exps = explanations if explanations is not None else _load_explanations()
    if not exps:
        return {"n": 0}

    valid_ratings = {"LOW", "MEDIUM", "HIGH"}
    n = len(exps)
    n_valid = sum(1 for e in exps if e.get("risk_rating") in valid_ratings)

    # Faithfulness: of explanations for records that DO contain red-flag terms,
    # how many actually reference at least one of the present terms?
    grounded_hits = grounded_total = 0
    high_with_flags = high_total = 0
    for e in exps:
        present = _present_red_flags(e["txn_purpose"])
        if present:
            grounded_total += 1
            expl = e["explanation"].lower()
            if any(term in expl for term in present):
                grounded_hits += 1
        if e.get("risk_rating") == "HIGH":
            high_total += 1
            if present:
                high_with_flags += 1

    rating_dist: dict[str, int] = {}
    for e in exps:
        rating_dist[e.get("risk_rating", "UNRATED")] = (
            rating_dist.get(e.get("risk_rating", "UNRATED"), 0) + 1
        )

    return {
        "n": n,
        "output_validity_rate": round(n_valid / n, 4),
        "faithfulness_recall": (
            round(grounded_hits / grounded_total, 4) if grounded_total else None
        ),
        "high_rating_precision": (
            round(high_with_flags / high_total, 4) if high_total else None
        ),
        "rating_distribution": rating_dist,
        "engines": sorted({e.get("engine", "unknown") for e in exps}),
    }


# --------------------------------------------------------------------------- #
# LLM-as-judge
# --------------------------------------------------------------------------- #
_JUDGE_PROMPT = """You are an evaluator scoring a financial-supervision AI's
explanation of a flagged transaction. Score from 1 (poor) to 5 (excellent)
based on: correctness, whether it justifies the risk rating with concrete
evidence from the transaction, and clarity for a human supervisor.

Transaction purpose: "{txn_purpose}"
Amount: {obs_value} {currency}
Model risk rating: {risk_rating}
Explanation to score:
{explanation}

Respond with ONLY a single integer from 1 to 5."""


def _judge_llm(exp: dict) -> int | None:
    try:
        from langchain_ollama import OllamaLLM
    except Exception:
        try:
            from langchain_community.llms import Ollama as OllamaLLM  # type: ignore
        except Exception:
            return None
    try:
        llm = OllamaLLM(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_BASE_URL)
        out = llm.invoke(_JUDGE_PROMPT.format(**exp))
        for ch in out:
            if ch in "12345":
                return int(ch)
        return None
    except Exception:
        return None


def _judge_rule_based(exp: dict) -> int:
    """Deterministic rubric proxy so judging runs offline."""
    score = 1
    if exp.get("risk_rating") in {"LOW", "MEDIUM", "HIGH"}:
        score += 1
    present = _present_red_flags(exp["txn_purpose"])
    expl = exp["explanation"].lower()
    if present and any(t in expl for t in present):
        score += 1  # grounded in the actual evidence
    if str(int(exp.get("obs_value", 0))) [:3] in exp["explanation"].replace(",", ""):
        score += 1  # references the amount
    if exp["explanation"].count("\n") >= 3 or "1." in exp["explanation"]:
        score += 1  # shows structured step-by-step reasoning
    return min(score, 5)


def judge_explanations(explanations: list[dict] | None = None) -> dict:
    exps = explanations if explanations is not None else _load_explanations()
    if not exps:
        return {"n": 0}
    scores, engine = [], "rule-based"
    for e in exps:
        s = _judge_llm(e)
        if s is None:
            s = _judge_rule_based(e)
        else:
            engine = "ollama"
        scores.append(s)
    dist: dict[str, int] = {}
    for s in scores:
        dist[str(s)] = dist.get(str(s), 0) + 1
    return {
        "n": len(scores),
        "judge_engine": engine,
        "avg_score": round(sum(scores) / len(scores), 3),
        "score_distribution": dist,
    }


def compute() -> dict:
    rows = _load_classified()
    result = {
        "detection": detection_metrics(rows),
        "threshold_sweep": threshold_sweep(rows),
    }
    try:
        exps = _load_explanations()
        result["llm_output"] = llm_output_metrics(exps)
        result["llm_as_judge"] = judge_explanations(exps)
    except FileNotFoundError:
        result["llm_output"] = {"n": 0, "note": "run stage 4 to evaluate explanations"}
    return result


if __name__ == "__main__":
    print(json.dumps(compute(), indent=2, default=str))
