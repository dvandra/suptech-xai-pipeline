"""Supervisory business analytics over the classified pipeline output.

Uses DuckDB to compute the aggregates a financial supervisor actually cares
about: where anomalies concentrate, how much value they represent, and how the
data-governance (FMR rejection) picture looks. Results are returned as plain
Python dicts so they can be serialised to JSON, served over the API, or
rendered in the dashboard / HTML report.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


def _rows(cur) -> list[dict]:
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def compute() -> dict:
    if not config.CLASSIFIED_JSONL.exists():
        raise FileNotFoundError(
            f"{config.CLASSIFIED_JSONL} not found - run the pipeline first "
            f"(python run_demo.py)."
        )

    con = duckdb.connect()
    con.execute(
        f"""
        CREATE OR REPLACE TABLE c AS
        SELECT * FROM read_json_auto('{config.CLASSIFIED_JSONL.as_posix()}');
        """
    )

    totals = _rows(
        con.execute(
            """
            SELECT
                count(*)                                   AS observations,
                sum(CASE WHEN is_anomaly THEN 1 ELSE 0 END) AS anomalies,
                round(avg(CASE WHEN is_anomaly THEN 1.0 ELSE 0.0 END), 4) AS anomaly_rate,
                round(sum(CASE WHEN is_anomaly THEN obs_value ELSE 0 END), 2) AS flagged_value,
                round(sum(obs_value), 2)                   AS total_value
            FROM c;
            """
        )
    )[0]

    by_ref_area = _rows(
        con.execute(
            """
            SELECT ref_area,
                   count(*) AS observations,
                   sum(CASE WHEN is_anomaly THEN 1 ELSE 0 END) AS anomalies,
                   round(avg(CASE WHEN is_anomaly THEN 1.0 ELSE 0.0 END), 4) AS anomaly_rate,
                   round(sum(CASE WHEN is_anomaly THEN obs_value ELSE 0 END), 2) AS flagged_value
            FROM c GROUP BY ref_area ORDER BY flagged_value DESC;
            """
        )
    )

    by_asset_class = _rows(
        con.execute(
            """
            SELECT asset_class,
                   count(*) AS observations,
                   sum(CASE WHEN is_anomaly THEN 1 ELSE 0 END) AS anomalies,
                   round(avg(CASE WHEN is_anomaly THEN 1.0 ELSE 0.0 END), 4) AS anomaly_rate
            FROM c GROUP BY asset_class ORDER BY anomalies DESC;
            """
        )
    )

    top_institutions = _rows(
        con.execute(
            """
            SELECT institution_id,
                   sum(CASE WHEN is_anomaly THEN 1 ELSE 0 END) AS anomalies,
                   round(sum(CASE WHEN is_anomaly THEN obs_value ELSE 0 END), 2) AS flagged_value
            FROM c
            GROUP BY institution_id
            HAVING anomalies > 0
            ORDER BY flagged_value DESC
            LIMIT 10;
            """
        )
    )

    anomalies_over_time = _rows(
        con.execute(
            """
            SELECT time_period,
                   count(*) AS observations,
                   sum(CASE WHEN is_anomaly THEN 1 ELSE 0 END) AS anomalies
            FROM c GROUP BY time_period ORDER BY time_period;
            """
        )
    )

    # Data-governance KPI: FMR rejection rate (if the raw + validated files exist).
    governance = _governance_kpis()

    con.close()
    return {
        "totals": totals,
        "by_ref_area": by_ref_area,
        "by_asset_class": by_asset_class,
        "top_institutions": top_institutions,
        "anomalies_over_time": anomalies_over_time,
        "governance": governance,
    }


def _governance_kpis() -> dict:
    raw = config.RAW_CSV
    validated = config.VALIDATED_JSONL
    if not (raw.exists() and validated.exists()):
        return {}
    con = duckdb.connect()
    n_raw = con.execute(
        f"SELECT count(*) FROM read_csv_auto('{raw.as_posix()}', header=true)"
    ).fetchone()[0]
    n_valid = con.execute(
        f"SELECT count(*) FROM read_json_auto('{validated.as_posix()}')"
    ).fetchone()[0]
    con.close()
    rejected = n_raw - n_valid
    return {
        "submissions": n_raw,
        "accepted": n_valid,
        "rejected": rejected,
        "rejection_rate": round(rejected / n_raw, 4) if n_raw else 0.0,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(compute(), indent=2, default=str))
