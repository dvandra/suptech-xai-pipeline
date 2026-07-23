"""End-to-end local demo of the SupTech-XAI pipeline.

Runs every stage in-process with no external services required (no Kafka,
no containers, no Ollama). Each stage still uses its real implementation; where a
heavy/optional dependency is missing it transparently falls back so the whole
flow completes and produces a compliance report.

    python run_demo.py [--count N]

Stages:
    0. Generate mock SDMX submissions (with injected invalid + anomalous rows)
    1. Ingest & validate against the FMR structure definition
    2. Wrangle with DuckDB
    3. Embed + classify + score anomalies
    4. Explain flagged anomalies via Chain-of-Thought
    5. Analytics + AI evaluation (detector P/R/F1, LLM faithfulness, drift)
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import config
from data_generator.kafka_producer import run_local

ROOT = Path(__file__).resolve().parent


def _load(stage_file: str):
    """Import a numeric-prefixed stage module by path."""
    path = ROOT / "pipeline" / stage_file
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser(description="Run the full pipeline locally")
    ap.add_argument("--count", type=int, default=500)
    ap.add_argument("--invalid-rate", type=float, default=0.12)
    ap.add_argument("--anomaly-rate", type=float, default=0.06)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    config.ensure_dirs()

    print("\n=== Stage 0: generate submissions ===")
    run_local(args.count, args.invalid_rate, args.anomaly_rate, args.seed)

    print("\n=== Stage 1: ingest & FMR validation ===")
    ingest = _load("1_ingest_validate.py").run(source="local")

    print("\n=== Stage 2: DuckDB wrangling ===")
    _load("2_wrangle_duckdb.py").run()

    print("\n=== Stage 3: embed, classify & score anomalies ===")
    embed = _load("3_embed_classify.py").run()

    print("\n=== Stage 4: Chain-of-Thought explanations ===")
    explain = _load("4_explain_anomaly.py").run()

    print("\n=== Stage 5: analytics & AI evaluation ===")
    from analytics.run_analytics import run as run_analytics

    metrics = run_analytics(
        run_meta={
            "generator_count": args.count,
            "invalid_rate": args.invalid_rate,
            "anomaly_rate": args.anomaly_rate,
            "seed": args.seed,
            "xai_engine": explain["engine"],
            "prompt_version": explain.get("prompt_version", config.PROMPT_VERSION),
        }
    )
    det = metrics["evaluation"]["detection"]
    steps = metrics["evaluation"].get("llm_step_validation", {})

    print("\n=== Summary ===")
    print(f"  submissions ingested : {ingest['total']}")
    print(f"  rejected by FMR      : {ingest['rejected']}")
    print(f"  cleaned & analysed   : {embed['rows']}")
    print(f"  anomalies flagged    : {explain['anomalies']}")
    print(f"  XAI engine           : {explain['engine']}")
    print(f"  prompt version       : {explain.get('prompt_version')}")
    print(f"  detector P/R/F1      : {det['precision']}/{det['recall']}/{det['f1']}")
    print(f"  CoT step-pass rate   : {steps.get('all_steps_ok_rate')}")
    print(f"  anomaly report       : {config.ANOMALY_REPORT}")
    print(f"  analytics report     : {config.ANALYTICS_HTML}")
    print(f"  dev+analytics report : {config.DEV_ANALYTICS_MD}")
    print(f"  metrics json         : {config.METRICS_JSON}")


if __name__ == "__main__":
    main()
