"""Stable audit schema for LLM / RAG (and future) pipelines.

Contract (versioned): each event records *what ran*, *what it produced*,
*how it reasoned*, and *which checks passed/failed* — so auditors can
replay or sample without re-running models.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = "1.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ReasoningStep:
    """One human-readable reasoning unit inside a model/pipeline step."""

    step_id: str
    title: str
    detail: str
    evidence_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationCheck:
    """A single pass/fail (or scored) validation against a step output."""

    check_id: str
    name: str
    passed: bool
    severity: str = "error"  # error | warn | info
    message: str = ""
    score: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditEvent:
    """One auditable unit of work (retrieve, generate, explain, classify, …)."""

    pipeline: str  # e.g. llm_xai | rag | detector | custom
    stage: str  # e.g. stage4_explain | stage6_rag_retrieve | stage6_rag_generate
    step_name: str  # short machine name
    subject_id: str  # observation id, case id, etc.
    status: str = "ok"  # ok | failed | skipped
    run_id: str = ""
    event_id: str = field(default_factory=lambda: uuid4().hex[:16])
    schema_version: str = SCHEMA_VERSION
    ts: str = field(default_factory=_utc_now)
    model: str | None = None
    prompt_version: str | None = None
    engine: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    reasoning_steps: list[ReasoningStep] = field(default_factory=list)
    validations: list[ValidationCheck] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def all_checks_passed(self) -> bool:
        return all(v.passed for v in self.validations if v.severity == "error")

    def finalize_status(self) -> None:
        if self.validations and not self.all_checks_passed():
            self.status = "failed"
        elif self.status == "":
            self.status = "ok"

    def to_dict(self) -> dict[str, Any]:
        self.finalize_status()
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "run_id": self.run_id,
            "ts": self.ts,
            "pipeline": self.pipeline,
            "stage": self.stage,
            "step_name": self.step_name,
            "subject_id": self.subject_id,
            "status": self.status,
            "model": self.model,
            "prompt_version": self.prompt_version,
            "engine": self.engine,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "reasoning_steps": [s.to_dict() for s in self.reasoning_steps],
            "validations": [v.to_dict() for v in self.validations],
            "meta": self.meta,
            "checks_passed": self.all_checks_passed(),
            "n_checks": len(self.validations),
            "n_checks_failed": sum(
                1 for v in self.validations if not v.passed and v.severity == "error"
            ),
        }
