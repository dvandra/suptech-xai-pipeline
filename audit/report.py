"""Human-readable audit report for LLM / RAG explainability."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import config


def render(summary: dict, sample_events: list[dict] | None = None) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sample_events = sample_events or []
    lines = [
        "# SupTech-XAI — Explainability & Audit Report",
        "",
        f"_Generated {now}_",
        "",
        "Per-step audit of detector decisions, LLM Chain-of-Thought explanations, "
        "and RAG retrieve/generate stages. Each event carries reasoning steps and "
        "validation checks for independent review.",
        "",
        "See [`docs/AUDIT_AND_XAI.md`](../../docs/AUDIT_AND_XAI.md).",
        "",
        "## Run summary",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| Run id | `{summary.get('run_id')}` |",
        f"| Schema | `{summary.get('schema_version')}` |",
        f"| Events | {summary.get('n_events')} |",
        f"| Passed | {summary.get('n_ok')} |",
        f"| Failed | {summary.get('n_failed')} |",
        f"| Pass rate | {summary.get('pass_rate')} |",
        "",
        "### By pipeline",
        "",
        "| Pipeline | n | ok | failed |",
        "|---|---|---|---|",
    ]
    for name, m in (summary.get("by_pipeline") or {}).items():
        lines.append(
            f"| {name} | {m.get('n')} | {m.get('ok')} | {m.get('failed')} |"
        )

    lines += [
        "",
        "### By stage",
        "",
        "| Stage | n | ok | failed |",
        "|---|---|---|---|",
    ]
    for name, m in (summary.get("by_stage") or {}).items():
        lines.append(
            f"| {name} | {m.get('n')} | {m.get('ok')} | {m.get('failed')} |"
        )

    src = summary.get("source_counts") or {}
    if src:
        lines += [
            "",
            "### Source coverage",
            "",
            "| Source | Count |",
            "|---|---|",
        ]
        for k, v in src.items():
            lines.append(f"| {k} | {v} |")

    fails = summary.get("failures_sample") or []
    lines += ["", "## Failures (sample)", ""]
    if not fails:
        lines.append("_No failed error-severity checks in this run._")
    else:
        for f in fails[:15]:
            lines.append(
                f"- `{f.get('subject_id')}` · {f.get('pipeline')}/{f.get('stage')} · "
                f"failed={', '.join(f.get('failed_checks') or [])}"
            )

    if sample_events:
        lines += ["", "## Example audited steps", ""]
        for ev in sample_events[:5]:
            lines.append(
                f"### `{ev.get('subject_id')}` — {ev.get('pipeline')}/{ev.get('step_name')}"
            )
            lines.append("")
            lines.append(f"- status: **{ev.get('status')}** · model=`{ev.get('model')}` · engine=`{ev.get('engine')}`")
            if ev.get("reasoning_steps"):
                lines.append("- reasoning:")
                for rs in ev["reasoning_steps"][:4]:
                    detail = (rs.get("detail") or "").replace("\n", " ")[:160]
                    lines.append(f"  - **{rs.get('step_id')}** {rs.get('title')}: {detail}")
            if ev.get("validations"):
                lines.append("- validations:")
                for v in ev["validations"]:
                    mark = "PASS" if v.get("passed") else "FAIL"
                    lines.append(
                        f"  - [{mark}] `{v.get('check_id')}` — {v.get('name')}"
                        + (f" (score={v.get('score')})" if v.get("score") is not None else "")
                    )
            lines.append("")

    lines += [
        "## Artefacts",
        "",
        f"- Audit trail JSONL: `{config.AUDIT_JSONL.relative_to(config.ROOT)}`",
        f"- Audit summary JSON: `{config.AUDIT_SUMMARY_JSON.relative_to(config.ROOT)}`",
        f"- This report: `{config.AUDIT_REPORT_MD.relative_to(config.ROOT)}`",
        "",
        "## Extending for future use cases",
        "",
        "1. Add a validator function in `audit/validators.py`.",
        "2. Register it on `VALIDATORS` under a new pipeline key.",
        "3. Emit events via `AuditTracer.step(...)` or `audit.build` helpers.",
        "4. Re-run `python -m audit.run_audit` — report format stays stable.",
        "",
        "---",
        "",
        "_Synthetic data only · educational simulation._",
        "",
    ]
    return "\n".join(lines)


def write(summary: dict, sample_events: list[dict] | None = None) -> Path:
    config.ensure_dirs()
    text = render(summary, sample_events=sample_events)
    config.AUDIT_REPORT_MD.write_text(text)
    return config.AUDIT_REPORT_MD


def load_sample_events(n: int = 5) -> list[dict]:
    if not config.AUDIT_JSONL.exists():
        return []
    rows = []
    with config.AUDIT_JSONL.open() as fh:
        for line in fh:
            if not line.strip():
                continue
            rows.append(json.loads(line))
            if len(rows) >= 200:
                break
    # Prefer a mix: one failed if any, else first events across pipelines
    failed = [r for r in rows if r.get("status") == "failed" or not r.get("checks_passed")]
    ok = [r for r in rows if r.get("checks_passed")]
    sample = (failed[:2] + ok[: max(0, n - 2)])[:n]
    return sample
