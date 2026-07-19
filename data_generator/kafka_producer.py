"""Simulates a central bank pushing high-frequency SDMX banking submissions.

Two modes:

  * ``--local``  Write newline-delimited JSON to ``data/raw_submissions.jsonl``
                 so the whole pipeline runs without any broker installed.
  * (default)    Publish to a Kafka topic using ``confluent-kafka``.

Each record loosely follows the SDMX-JSON shape: a set of coded dimensions,
a numeric ``OBS_VALUE`` measure, and attributes including a free-text
``TXN_PURPOSE`` that the downstream AI stages analyse.

The generator deliberately injects a configurable fraction of:
  * structurally invalid records (bad codes / missing dims / non-numeric value)
    -> exercised by the FMR validation stage, and
  * semantic outliers (unusual transaction purposes / extreme amounts)
    -> exercised by the anomaly detection + XAI stages.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from metadata_registry import sdmx_csv  # noqa: E402

# Representative, "normal" transaction-purpose phrases per asset class. The
# embedding stage learns category centroids from these; outliers sit far away.
NORMAL_PURPOSES = {
    "LOAN": [
        "Corporate working capital facility drawdown",
        "Residential mortgage origination",
        "Syndicated term loan disbursement",
        "SME revolving credit line utilisation",
    ],
    "DEPOSIT": [
        "Retail time deposit placement",
        "Institutional overnight cash deposit",
        "Wholesale money market deposit",
        "Savings account interest accrual",
    ],
    "SECURITY": [
        "Government bond secondary market purchase",
        "Investment grade corporate bond settlement",
        "Equity index fund subscription",
        "Treasury bill primary auction allotment",
    ],
    "DERIVATIVE": [
        "Interest rate swap fixed leg payment",
        "FX forward contract rollover",
        "Credit default swap premium settlement",
        "Equity option premium collection",
    ],
    "FX": [
        "Spot foreign exchange conversion",
        "Cross-currency liquidity rebalancing",
        "Client remittance settlement",
        "Central bank swap line drawdown",
    ],
}

# Suspicious / anomalous free-text purposes used to seed outliers.
ANOMALOUS_PURPOSES = [
    "Urgent offshore transfer to unregistered shell entity no questions",
    "Structuring cash below reporting threshold across multiple accounts",
    "Payment to sanctioned counterparty routed via intermediary",
    "Layering funds through rapid round-trip cross-border wires",
    "Trade mis-invoicing to move value across jurisdictions",
]


def _random_time_period() -> str:
    start = date(2024, 1, 1)
    d = start + timedelta(days=random.randint(0, 540))
    return d.strftime("%Y-%m")


def _make_valid_record(rec_id: int, anomalous: bool) -> dict:
    asset = random.choice(config.CODELISTS["ASSET_CLASS"])
    if anomalous:
        purpose = random.choice(ANOMALOUS_PURPOSES)
        # Anomalous records also tend to carry extreme amounts.
        amount = round(random.uniform(50_000_000, 500_000_000), 2)
    else:
        purpose = random.choice(NORMAL_PURPOSES[asset])
        amount = round(random.uniform(1_000, 5_000_000), 2)

    return {
        "REF_AREA": random.choice(config.CODELISTS["REF_AREA"]),
        "INSTITUTION_ID": f"BANK{random.randint(1, 40):03d}",
        "ASSET_CLASS": asset,
        "TIME_PERIOD": _random_time_period(),
        "OBS_VALUE": amount,
        "CURRENCY": random.choice(config.CODELISTS["CURRENCY"]),
        "TXN_PURPOSE": purpose,
    }


def _corrupt_record(rec: dict) -> dict:
    """Introduce a structural violation the FMR should reject."""
    kind = random.choice(["bad_code", "missing_dim", "bad_measure"])
    rec = dict(rec)
    if kind == "bad_code":
        rec["REF_AREA"] = "XX"  # not in the REF_AREA codelist
    elif kind == "missing_dim":
        rec.pop("ASSET_CLASS", None)  # required dimension removed
    else:
        rec["OBS_VALUE"] = "N/A"  # measure not numeric
    rec["_injected_error"] = kind
    return rec


def generate(count: int, invalid_rate: float, anomaly_rate: float, seed: int):
    random.seed(seed)
    for i in range(count):
        anomalous = random.random() < anomaly_rate
        rec = _make_valid_record(i, anomalous)
        if random.random() < invalid_rate:
            rec = _corrupt_record(rec)
        yield rec


def run_local(count: int, invalid_rate: float, anomaly_rate: float, seed: int) -> Path:
    config.ensure_dirs()
    records = list(generate(count, invalid_rate, anomaly_rate, seed))
    out = sdmx_csv.write_csv(records, config.RAW_CSV)
    print(f"[producer] wrote {len(records)} SDMX-CSV submissions -> {out}")
    return out


def run_kafka(count: int, invalid_rate: float, anomaly_rate: float, seed: int):
    try:
        from confluent_kafka import Producer
    except ImportError:
        sys.exit(
            "confluent-kafka not installed. Use --local, or "
            "`pip install confluent-kafka` and start Kafka (make infra-up)."
        )

    producer = Producer({"bootstrap.servers": config.KAFKA_BOOTSTRAP})
    n = 0
    for i, rec in enumerate(generate(count, invalid_rate, anomaly_rate, seed)):
        # Each streamed message is a self-describing SDMX-JSON observation.
        msg = {"structure": config.DATAFLOW_REF, **rec}
        producer.produce(
            config.KAFKA_TOPIC,
            key=str(i),
            value=json.dumps(msg).encode("utf-8"),
        )
        n += 1
        if n % 100 == 0:
            producer.poll(0)
    producer.flush()
    print(f"[producer] published {n} submissions -> topic {config.KAFKA_TOPIC}")


def main():
    ap = argparse.ArgumentParser(description="Mock SDMX banking submission producer")
    ap.add_argument("--local", action="store_true", help="write to JSONL instead of Kafka")
    ap.add_argument("--count", type=int, default=500)
    ap.add_argument("--invalid-rate", type=float, default=0.12)
    ap.add_argument("--anomaly-rate", type=float, default=0.06)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if args.local:
        run_local(args.count, args.invalid_rate, args.anomaly_rate, args.seed)
    else:
        run_kafka(args.count, args.invalid_rate, args.anomaly_rate, args.seed)


if __name__ == "__main__":
    main()
