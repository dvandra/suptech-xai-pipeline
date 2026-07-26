"""In-memory + durable audit tracer for a single pipeline run."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

import config
from audit.schema import AuditEvent, ReasoningStep, ValidationCheck


class AuditTracer:
    """Collects AuditEvents and flushes them to JSONL + summary JSON."""

    def __init__(self, run_id: str | None = None, pipeline: str = "pipeline"):
        self.run_id = run_id or uuid4().hex[:12]
        self.pipeline = pipeline
        self.events: list[AuditEvent] = []

    def emit(self, event: AuditEvent) -> AuditEvent:
        if not event.run_id:
            event.run_id = self.run_id
        if not event.pipeline:
            event.pipeline = self.pipeline
        event.finalize_status()
        self.events.append(event)
        return event

    def step(
        self,
        *,
        stage: str,
        step_name: str,
        subject_id: str,
        pipeline: str | None = None,
        model: str | None = None,
        prompt_version: str | None = None,
        engine: str | None = None,
        inputs: dict | None = None,
        outputs: dict | None = None,
        reasoning_steps: Iterable[ReasoningStep] | None = None,
        validations: Iterable[ValidationCheck] | None = None,
        meta: dict | None = None,
        status: str = "ok",
    ) -> AuditEvent:
        event = AuditEvent(
            pipeline=pipeline or self.pipeline,
            stage=stage,
            step_name=step_name,
            subject_id=subject_id,
            status=status,
            run_id=self.run_id,
            model=model,
            prompt_version=prompt_version,
            engine=engine,
            inputs=inputs or {},
            outputs=outputs or {},
            reasoning_steps=list(reasoning_steps or []),
            validations=list(validations or []),
            meta=meta or {},
        )
        return self.emit(event)

    def summary(self) -> dict[str, Any]:
        by_pipeline: dict[str, dict[str, int]] = {}
        by_stage: dict[str, dict[str, int]] = {}
        failed_subjects: list[dict[str, Any]] = []
        n_ok = n_failed = 0
        for e in self.events:
            d = e.to_dict()
            if d["status"] == "failed" or not d["checks_passed"]:
                n_failed += 1
                failed_subjects.append(
                    {
                        "event_id": d["event_id"],
                        "pipeline": d["pipeline"],
                        "stage": d["stage"],
                        "subject_id": d["subject_id"],
                        "failed_checks": [
                            v["check_id"]
                            for v in d["validations"]
                            if not v["passed"] and v["severity"] == "error"
                        ],
                    }
                )
            else:
                n_ok += 1
            bp = by_pipeline.setdefault(d["pipeline"], {"ok": 0, "failed": 0, "n": 0})
            bs = by_stage.setdefault(d["stage"], {"ok": 0, "failed": 0, "n": 0})
            key = "failed" if d["status"] == "failed" or not d["checks_passed"] else "ok"
            bp[key] += 1
            bp["n"] += 1
            bs[key] += 1
            bs["n"] += 1

        return {
            "run_id": self.run_id,
            "schema_version": "1.0",
            "n_events": len(self.events),
            "n_ok": n_ok,
            "n_failed": n_failed,
            "pass_rate": round(n_ok / len(self.events), 4) if self.events else None,
            "by_pipeline": by_pipeline,
            "by_stage": by_stage,
            "failures_sample": failed_subjects[:25],
        }

    def flush(
        self,
        jsonl_path: Path | None = None,
        summary_path: Path | None = None,
        append: bool = False,
    ) -> dict[str, Any]:
        config.ensure_dirs()
        jsonl_path = jsonl_path or config.AUDIT_JSONL
        summary_path = summary_path or config.AUDIT_SUMMARY_JSON
        mode = "a" if append else "w"
        with jsonl_path.open(mode) as fh:
            for e in self.events:
                fh.write(json.dumps(e.to_dict(), default=str) + "\n")
        summary = self.summary()
        summary_path.write_text(json.dumps(summary, indent=2, default=str))
        return summary
