"""Cross-cutting explainability, validation, and audit trail.

Every LLM / RAG step can emit a structured ``AuditEvent`` with reasoning
steps and validation outcomes. Designed so future pipelines register new
validators without changing the store or report format.
"""

from audit.schema import AuditEvent, ReasoningStep, ValidationCheck
from audit.tracer import AuditTracer

__all__ = [
    "AuditEvent",
    "ReasoningStep",
    "ValidationCheck",
    "AuditTracer",
]
