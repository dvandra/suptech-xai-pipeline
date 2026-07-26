"""Build the cross-pipeline explainability / audit trail.

Reads Stage 3–6 artefacts (classified rows, explanations, RAG results) and
emits:

  * data/audit_trail.jsonl
  * data/audit_summary.json
  * data/reports/audit_report.md

    python -m audit.run_audit
    make audit
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from audit.build import build_full_audit  # noqa: E402
from audit.report import load_sample_events, write as write_report  # noqa: E402


def run(run_id: str | None = None) -> dict:
    config.ensure_dirs()
    tracer, summary = build_full_audit(run_id=run_id)
    samples = [e.to_dict() for e in tracer.events[:8]]
    # Prefer mixed sample from flushed JSONL
    samples = load_sample_events(6) or samples
    path = write_report(summary, sample_events=samples)
    print(f"[audit] trail   -> {config.AUDIT_JSONL}")
    print(f"[audit] summary -> {config.AUDIT_SUMMARY_JSON}")
    print(f"[audit] report  -> {path}")
    print(
        f"[audit] events={summary.get('n_events')} "
        f"pass_rate={summary.get('pass_rate')} "
        f"failed={summary.get('n_failed')}"
    )
    return summary


if __name__ == "__main__":
    run()
