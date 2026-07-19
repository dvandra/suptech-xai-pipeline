"""Stage 1 - Ingest & SDMX validation (RegTech / data governance).

Consumes incoming submissions and validates them against the DSD via the FMR:

  * local mode reads an SDMX-CSV dataset and POSTs it to the FMR data-validation
    web service (``/ws/public/data/validate``), exactly as a reporter's file
    would be validated in production;
  * Kafka mode consumes SDMX-JSON observations from the topic.

If the FMR REST API is unreachable, validation falls back to the in-process
validator (identical logic) so the pipeline still runs offline. Either way the
result is an FMR-style validation report whose ``Position`` entries identify the
non-compliant observations, which are rejected before any analytics run.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from metadata_registry import sdmx_csv  # noqa: E402
from metadata_registry.validator import validate_dataset  # noqa: E402


def _fmr_api_available() -> bool:
    try:
        import requests

        r = requests.get(f"{config.FMR_BASE_URL}/health", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def _validate_via_api(records: list[dict]) -> dict:
    """POST the dataset as SDMX-CSV to the FMR data-validation web service."""
    import requests

    csv_body = sdmx_csv.to_csv_string(records)
    resp = requests.post(
        config.FMR_VALIDATE_ENDPOINT,
        data=csv_body.encode("utf-8"),
        headers={"Content-Type": "text/csv"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _load_local() -> list[dict]:
    if not config.RAW_CSV.exists():
        sys.exit(
            f"{config.RAW_CSV} not found. Generate data first:\n"
            f"  python data_generator/kafka_producer.py --local"
        )
    return sdmx_csv.read_csv(config.RAW_CSV)


def _load_kafka(max_messages: int) -> list[dict]:
    from confluent_kafka import Consumer

    consumer = Consumer(
        {
            "bootstrap.servers": config.KAFKA_BOOTSTRAP,
            "group.id": config.KAFKA_GROUP,
            "auto.offset.reset": "earliest",
        }
    )
    consumer.subscribe([config.KAFKA_TOPIC])
    records, got = [], 0
    try:
        while got < max_messages:
            msg = consumer.poll(2.0)
            if msg is None:
                break
            if msg.error():
                continue
            obs = json.loads(msg.value().decode("utf-8"))
            obs.pop("structure", None)
            records.append(obs)
            got += 1
    finally:
        consumer.close()
    return records


def run(source: str = "local", max_messages: int = 100_000) -> dict:
    config.ensure_dirs()
    records = _load_local() if source == "local" else _load_kafka(max_messages)

    use_api = _fmr_api_available()
    if use_api:
        report = _validate_via_api(records)
        via = f"FMR REST API ({config.FMR_VALIDATE_ENDPOINT})"
    else:
        report = validate_dataset(records)
        via = "in-process validator (FMR offline)"
    print(f"[ingest] validated {len(records)} observations via {via}")

    invalid_positions = {e["Position"] for e in report.get("ValidationReport", [])}

    accepted = 0
    with config.VALIDATED_JSONL.open("w") as out:
        for pos, rec in enumerate(records):
            if pos in invalid_positions:
                continue
            clean = {c: rec.get(c, "") for c in config.COMPONENTS}
            out.write(json.dumps(clean) + "\n")
            accepted += 1

    rejected = len(records) - accepted
    print(
        f"[ingest] accepted={accepted} rejected={rejected} "
        f"(errors={report.get('ErrorCount', 0)}) -> {config.VALIDATED_JSONL}"
    )
    return {
        "total": len(records),
        "accepted": accepted,
        "rejected": rejected,
        "error_count": report.get("ErrorCount", 0),
    }


def main():
    ap = argparse.ArgumentParser(description="Ingest & validate submissions")
    ap.add_argument("--source", choices=["local", "kafka"], default="local")
    ap.add_argument("--max-messages", type=int, default=100_000)
    args = ap.parse_args()
    run(args.source, args.max_messages)


if __name__ == "__main__":
    main()
