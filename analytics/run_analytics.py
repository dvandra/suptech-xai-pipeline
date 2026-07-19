"""Stage 5 - compute the full analytics + AI-evaluation bundle.

Reads the pipeline artifacts (classified records + structured explanations),
computes supervisory analytics, model/LLM evaluation and drift, then writes:

  * data/metrics.json                 - machine-readable, served by the API
  * data/reports/analytics_report.html - self-contained visual report

Run after the pipeline:  python analytics/run_analytics.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from analytics import drift, evaluation, report, supervisory  # noqa: E402


def compute_all() -> dict:
    return {
        "dataflow": config.DATAFLOW_REF,
        "supervisory": supervisory.compute(),
        "evaluation": evaluation.compute(),
        "drift": drift.compute(),
    }


def run() -> dict:
    config.ensure_dirs()
    metrics = compute_all()

    config.METRICS_JSON.write_text(json.dumps(metrics, indent=2, default=str))
    report.write(metrics)

    det = metrics["evaluation"]["detection"]
    llm = metrics["evaluation"].get("llm_output", {})
    judge = metrics["evaluation"].get("llm_as_judge", {})
    print(f"[analytics] metrics -> {config.METRICS_JSON}")
    print(f"[analytics] report  -> {config.ANALYTICS_HTML}")
    print(
        f"[analytics] detector P/R/F1 = {det['precision']}/{det['recall']}/{det['f1']} "
        f"| LLM validity={llm.get('output_validity_rate')} "
        f"faithfulness={llm.get('faithfulness_recall')} "
        f"judge={judge.get('avg_score')}"
    )
    return metrics


if __name__ == "__main__":
    run()
