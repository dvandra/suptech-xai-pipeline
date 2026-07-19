"""SDMX structural validation logic (the core the FMR mock wraps).

Emulates what a real Fusion Metadata Registry does when validating a data
message against a Data Structure Definition (DSD):

  * every required dimension is present,
  * coded dimensions/attributes carry values from their codelist,
  * the observation measure is numeric,
  * the time period matches the expected reporting format,
  * no duplicate observations share the same series key + time period.

``validate_dataset`` returns an FMR-style JSON validation report whose entries
carry the row ``Position`` (as FMR does), so a consumer can map errors back to
the offending observations.
"""
from __future__ import annotations

import re
from typing import Any

import config

_TIME_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _record_errors(record: dict[str, Any]) -> list[dict]:
    """Structural errors for a single observation (no cross-row checks)."""
    errors: list[dict] = []

    def err(component: str, code: str, message: str) -> None:
        errors.append(
            {"Severity": "Error", "Component": component, "Code": code,
             "Message": message}
        )

    # 1. Required dimensions present and coded correctly.
    for dim in config.DIMENSIONS:
        if record.get(dim) in (None, ""):
            err(dim, "MANDATORY_MISSING", f"missing required dimension '{dim}'")
            continue
        if dim in config.CODELISTS and record[dim] not in config.CODELISTS[dim]:
            err(dim, "CODE_NOT_IN_CODELIST",
                f"value '{record[dim]}' for '{dim}' is not in its codelist")

    # 2. TIME_PERIOD format (SDMX reporting period).
    tp = record.get(config.TIME_DIMENSION)
    if tp not in (None, "") and not _TIME_PERIOD_RE.match(str(tp)):
        err(config.TIME_DIMENSION, "INVALID_TIME_FORMAT",
            f"TIME_PERIOD '{tp}' does not match YYYY-MM")

    # 3. Measure must be present and numeric.
    if record.get(config.MEASURE) in (None, ""):
        err(config.MEASURE, "MANDATORY_MISSING", f"missing measure '{config.MEASURE}'")
    else:
        try:
            float(record[config.MEASURE])
        except (TypeError, ValueError):
            err(config.MEASURE, "INVALID_MEASURE_REPRESENTATION",
                f"measure '{config.MEASURE}' value '{record[config.MEASURE]}' is not numeric")

    # 4. Coded attributes must respect their codelist.
    for attr in config.ATTRIBUTES:
        if attr in config.CODELISTS and record.get(attr) not in (None, ""):
            if record[attr] not in config.CODELISTS[attr]:
                err(attr, "CODE_NOT_IN_CODELIST",
                    f"attribute value '{record[attr]}' for '{attr}' is not in its codelist")

    return errors


def validate_record(record: dict[str, Any]) -> dict[str, Any]:
    """Validate one observation; convenience wrapper around _record_errors."""
    errors = _record_errors(record)
    return {
        "dataflow": config.DATAFLOW_REF,
        "valid": len(errors) == 0,
        "errors": [e["Message"] for e in errors],
    }


def _series_key(record: dict) -> tuple:
    return tuple(record.get(d, "") for d in config.DIMENSIONS)


def validate_dataset(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate a whole dataset, returning an FMR-style JSON report."""
    report: list[dict] = []
    seen: dict[tuple, int] = {}

    for pos, rec in enumerate(records):
        for e in _record_errors(rec):
            report.append({"Position": pos, **e})

        # Cross-row check: duplicate observation (same series key + time).
        key = _series_key(rec)
        if all(v not in (None, "") for v in key):
            if key in seen:
                report.append({
                    "Position": pos, "Severity": "Error",
                    "Component": "SERIES_KEY", "Code": "DUPLICATE_OBSERVATION",
                    "Message": (f"duplicate observation for series key {key} "
                                f"(first seen at position {seen[key]})"),
                })
            else:
                seen[key] = pos

    invalid_positions = sorted({e["Position"] for e in report})
    return {
        "Success": True,
        "Errors": len(report) > 0,
        "DataStructure": config.DSD_URN,
        "Dataflow": config.DATAFLOW_REF,
        "ObservationsProcessed": len(records),
        "ErrorCount": len(report),
        "InvalidObservations": len(invalid_positions),
        "ValidationReport": report,
    }
