"""Stage 5 - compute the full analytics + AI-evaluation bundle.

Reads the pipeline artifacts (classified records + structured explanations),
computes supervisory analytics, model/LLM evaluation and drift, then writes:

  * data/metrics.json                      - machine-readable, served by the API
  * data/reports/analytics_report.html     - visual analytics report
  * data/reports/dev_analytics_report.md   - developer + analytics report

Run after the pipeline:  python analytics/run_analytics.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from analytics import (  # noqa: E402
    charts,
    dev_report,
    drift,
    evaluation,
    report,
    supervisory,
)


def compute_all() -> dict:
    return {
        "dataflow": config.DATAFLOW_REF,
        "config": {
            "prompt_version": config.PROMPT_VERSION,
            "ollama_model": config.OLLAMA_MODEL,
            "ollama_judge_model": config.OLLAMA_JUDGE_MODEL,
            "anomaly_sigma": config.ANOMALY_SIGMA,
        },
        "supervisory": supervisory.compute(),
        "evaluation": evaluation.compute(),
        "drift": drift.compute(),
    }


def run(run_meta: dict | None = None) -> dict:
    config.ensure_dirs()
    metrics = compute_all()

    config.METRICS_JSON.write_text(json.dumps(metrics, indent=2, default=str))
    report.write(metrics)
    dev_report.write(metrics, run_meta=run_meta)
    chart_paths = charts.write_charts(metrics=metrics)

    det = metrics["evaluation"]["detection"]
    llm = metrics["evaluation"].get("llm_output", {})
    judge = metrics["evaluation"].get("llm_as_judge", {})
    steps = metrics["evaluation"].get("llm_step_validation", {})
    print(f"[analytics] metrics     -> {config.METRICS_JSON}")
    print(f"[analytics] html report -> {config.ANALYTICS_HTML}")
    print(f"[analytics] dev report  -> {config.DEV_ANALYTICS_MD}")
    print(f"[analytics] charts      -> {len(chart_paths)} SVGs in {charts.CHARTS_DIR}")
    print(
        f"[analytics] detector P/R/F1 = {det['precision']}/{det['recall']}/{det['f1']} "
        f"| LLM validity={llm.get('output_validity_rate')} "
        f"faithfulness={llm.get('faithfulness_recall')} "
        f"step-pass={steps.get('all_steps_ok_rate')} "
        f"judge={judge.get('avg_score')}"
    )
    return metrics


if __name__ == "__main__":
    run()
