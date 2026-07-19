"""Minimal SDMX-CSV (2.0) reader/writer.

SDMX-CSV is one of the official SDMX data-exchange formats and is directly
readable by the Fusion Metadata Registry. The layout is:

    STRUCTURE,STRUCTURE_ID,ACTION,<component columns...>
    dataflow,DEMO:BANKING_FLOWS_FLOW(1.0),I,US,BANK001,LOAN,2024-05,1000.0,USD,"..."

* STRUCTURE     - the artefact type the data is reported against (dataflow here)
* STRUCTURE_ID  - agency:id(version) of that artefact
* ACTION        - I (informational/append), A (append), D (delete), R (replace)
* remaining columns are the DSD components (dimensions, measure, attributes)

We keep component values as raw strings on read so that malformed values (e.g.
a non-numeric OBS_VALUE, or an empty required dimension) survive to the
validator, exactly as they would arriving from an external reporter.
"""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

_META_COLS = ["STRUCTURE", "STRUCTURE_ID", "ACTION"]
HEADER = _META_COLS + config.COMPONENTS


def _row_for(record: dict, action: str = "I") -> dict:
    row = {
        "STRUCTURE": "dataflow",
        "STRUCTURE_ID": config.DATAFLOW_REF,
        "ACTION": action,
    }
    for comp in config.COMPONENTS:
        val = record.get(comp, "")
        row[comp] = "" if val is None else str(val)
    return row


def write_csv(records: list[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=HEADER)
        writer.writeheader()
        for rec in records:
            writer.writerow(_row_for(rec))
    return path


def to_csv_string(records: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=HEADER)
    writer.writeheader()
    for rec in records:
        writer.writerow(_row_for(rec))
    return buf.getvalue()


def _parse_rows(reader: csv.DictReader) -> list[dict]:
    records = []
    for raw in reader:
        rec = {comp: (raw.get(comp) or "") for comp in config.COMPONENTS}
        rec["_structure_id"] = raw.get("STRUCTURE_ID", "")
        records.append(rec)
    return records


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        return _parse_rows(csv.DictReader(fh))


def parse_csv_string(text: str) -> list[dict]:
    return _parse_rows(csv.DictReader(io.StringIO(text)))
