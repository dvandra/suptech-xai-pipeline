"""Metrics API - exposes the analytics/evaluation results over REST.

Metrics are computed on demand from the current pipeline artifacts.

Run:
    uvicorn analytics.metrics_api:app --reload --port 8001
"""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from analytics import drift, evaluation, supervisory  # noqa: E402

app = FastAPI(
    title="SupTech-XAI Metrics API",
    description="Supervisory analytics, AI evaluation and drift metrics.",
    version="1.0.0",
)


def _guard(fn):
    try:
        return fn()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "dataflow": config.DATAFLOW_REF}


@app.get("/metrics/summary")
def summary() -> dict:
    return _guard(supervisory.compute)


@app.get("/metrics/evaluation")
def eval_metrics() -> dict:
    return _guard(evaluation.compute)


@app.get("/metrics/drift")
def drift_metrics() -> dict:
    return _guard(drift.compute)


@app.get("/metrics/all")
def all_metrics() -> dict:
    return {
        "supervisory": _guard(supervisory.compute),
        "evaluation": _guard(evaluation.compute),
        "drift": _guard(drift.compute),
    }
