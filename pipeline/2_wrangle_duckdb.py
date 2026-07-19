"""Stage 2 - High-speed wrangling with DuckDB.

Loads the validated SDMX submissions into DuckDB and uses vectorised SQL to:
  * cast the measure to a proper numeric type,
  * normalise / trim the coded dimensions,
  * drop exact duplicate observations,
  * isolate the unstructured ``TXN_PURPOSE`` text for downstream AI analysis.

Output is written as Parquet - a columnar format suited to the analytical
layer - for the embedding stage to consume.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


def run() -> int:
    config.ensure_dirs()
    if not config.VALIDATED_JSONL.exists():
        sys.exit(f"{config.VALIDATED_JSONL} not found. Run stage 1 first.")

    con = duckdb.connect()
    con.execute(
        f"""
        CREATE OR REPLACE TABLE raw AS
        SELECT * FROM read_json_auto('{config.VALIDATED_JSONL.as_posix()}');
        """
    )

    # Vectorised cleaning + flattening. DuckDB reads the JSON columns directly.
    con.execute(
        f"""
        CREATE OR REPLACE TABLE clean AS
        SELECT DISTINCT
            -- SDMX observation identity = series key (dimensions) + time period.
            concat_ws('.', upper(trim(REF_AREA)), trim(INSTITUTION_ID),
                      upper(trim(ASSET_CLASS)), TIME_PERIOD) AS id,
            upper(trim(REF_AREA))       AS ref_area,
            trim(INSTITUTION_ID)        AS institution_id,
            upper(trim(ASSET_CLASS))    AS asset_class,
            TIME_PERIOD                 AS time_period,
            CAST(OBS_VALUE AS DOUBLE)   AS obs_value,
            upper(trim(CURRENCY))       AS currency,
            trim(TXN_PURPOSE)           AS txn_purpose
        FROM raw
        WHERE TXN_PURPOSE IS NOT NULL
          AND length(trim(TXN_PURPOSE)) > 0;
        """
    )

    n = con.execute("SELECT count(*) FROM clean").fetchone()[0]
    by_class = con.execute(
        "SELECT asset_class, count(*) c FROM clean GROUP BY 1 ORDER BY c DESC"
    ).fetchall()

    con.execute(
        f"""
        COPY clean TO '{config.WRANGLED_PARQUET.as_posix()}' (FORMAT PARQUET);
        """
    )
    con.close()

    print(f"[wrangle] cleaned rows={n} -> {config.WRANGLED_PARQUET}")
    print(f"[wrangle] by asset_class: {dict(by_class)}")
    return n


if __name__ == "__main__":
    run()
