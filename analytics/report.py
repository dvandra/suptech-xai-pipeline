"""Render the computed metrics into a self-contained static HTML report.

No JS libraries or servers required - charts are pure CSS/SVG - so the file
opens anywhere and can be published on GitHub Pages.
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

_CSS = """
:root{--bg:#0f172a;--card:#1e293b;--ink:#e2e8f0;--mut:#94a3b8;--acc:#38bdf8;
--hi:#f87171;--md:#fbbf24;--lo:#4ade80}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:32px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:18px;margin:28px 0 12px;
border-bottom:1px solid #334155;padding-bottom:6px}
.sub{color:var(--mut);margin:0 0 24px}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(180px,1fr))}
.card{background:var(--card);border:1px solid #334155;border-radius:12px;padding:16px}
.kpi{font-size:28px;font-weight:700;color:var(--acc)}
.kpi.hi{color:var(--hi)}.label{color:var(--mut);font-size:13px;text-transform:uppercase;
letter-spacing:.04em}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #334155}
th{color:var(--mut);font-weight:600}
.bar{height:9px;background:#334155;border-radius:5px;overflow:hidden}
.bar>span{display:block;height:100%;background:var(--acc)}
.badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600}
.stable{background:#064e3b;color:#4ade80}.moderate{background:#78350f;color:#fbbf24}
.major{background:#7f1d1d;color:#f87171}
.foot{color:var(--mut);font-size:12px;margin-top:32px}
"""


def _kpi(label: str, value, hi: bool = False) -> str:
    cls = "kpi hi" if hi else "kpi"
    return f'<div class="card"><div class="{cls}">{value}</div><div class="label">{html.escape(label)}</div></div>'


def _table(headers: list[str], rows: list[list]) -> str:
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = ""
    for r in rows:
        body += "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r) + "</tr>"
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _bar_rows(items: list[tuple[str, float]], fmt=str) -> str:
    mx = max((v for _, v in items), default=1) or 1
    out = ""
    for name, v in items:
        pct = 100 * v / mx
        out += (
            f'<tr><td>{html.escape(str(name))}</td>'
            f'<td style="width:55%"><div class="bar"><span style="width:{pct:.1f}%"></span></div></td>'
            f'<td>{fmt(v)}</td></tr>'
        )
    return f"<table><tbody>{out}</tbody></table>"


def render(metrics: dict) -> str:
    sup = metrics.get("supervisory", {})
    ev = metrics.get("evaluation", {})
    drift = metrics.get("drift", {})

    totals = sup.get("totals", {})
    det = ev.get("detection", {})
    sweep = ev.get("threshold_sweep", {})
    llm = ev.get("llm_output", {})
    judge = ev.get("llm_as_judge", {})

    parts = [f"<style>{_CSS}</style>", "<h1>SupTech-XAI &mdash; Analytics &amp; AI Evaluation</h1>",
             f'<p class="sub">Dataflow <code>{html.escape(config.DATAFLOW_REF)}</code> '
             f'&middot; produced by the Stage&nbsp;5 analytics layer</p>']

    # Supervisory KPIs
    parts.append("<h2>Supervisory overview</h2><div class='grid'>")
    parts.append(_kpi("observations", totals.get("observations", "-")))
    parts.append(_kpi("anomalies", totals.get("anomalies", "-"), hi=True))
    parts.append(_kpi("anomaly rate", f'{totals.get("anomaly_rate", 0)*100:.1f}%'))
    parts.append(_kpi("flagged value", f'{totals.get("flagged_value", 0):,.0f}'))
    gov = sup.get("governance", {})
    if gov:
        parts.append(_kpi("FMR rejection rate", f'{gov.get("rejection_rate",0)*100:.1f}%'))
    parts.append("</div>")

    if sup.get("by_ref_area"):
        parts.append("<h2>Flagged value by jurisdiction</h2>")
        parts.append(_bar_rows(
            [(r["ref_area"], r["flagged_value"]) for r in sup["by_ref_area"]],
            fmt=lambda v: f"{v:,.0f}"))

    if sup.get("by_asset_class"):
        parts.append("<h2>Anomalies by asset class</h2>")
        parts.append(_table(
            ["asset class", "observations", "anomalies", "anomaly rate"],
            [[r["asset_class"], r["observations"], r["anomalies"], f'{r["anomaly_rate"]*100:.1f}%']
             for r in sup["by_asset_class"]]))

    # Evaluation
    parts.append("<h2>AI evaluation &mdash; anomaly detector</h2><div class='grid'>")
    parts.append(_kpi("precision", det.get("precision", "-")))
    parts.append(_kpi("recall", det.get("recall", "-")))
    parts.append(_kpi("F1", det.get("f1", "-")))
    parts.append(_kpi("accuracy", det.get("accuracy", "-")))
    parts.append("</div>")
    cm = det.get("confusion_matrix", {})
    if cm:
        parts.append(_table(["", "predicted +", "predicted -"],
                            [["actual +", cm["tp"], cm["fn"]],
                             ["actual -", cm["fp"], cm["tn"]]]))
    if sweep.get("best_operating_point"):
        b = sweep["best_operating_point"]
        parts.append(
            f'<p class="sub">F1-optimal threshold at <b>sigma={b["sigma"]}</b> '
            f'(F1={b["f1"]}); currently configured sigma={sweep.get("current_sigma")}.</p>')

    # LLM evaluation
    parts.append("<h2>AI evaluation &mdash; LLM explanations</h2><div class='grid'>")
    parts.append(_kpi("output validity", f'{(llm.get("output_validity_rate") or 0)*100:.0f}%'))
    fr = llm.get("faithfulness_recall")
    parts.append(_kpi("faithfulness recall", f'{fr*100:.0f}%' if fr is not None else "n/a"))
    if judge.get("avg_score") is not None:
        parts.append(_kpi(f'LLM-as-judge ({judge.get("judge_engine","")})',
                          f'{judge["avg_score"]}/5'))
    parts.append("</div>")
    if llm.get("rating_distribution"):
        parts.append("<h2>Risk-rating distribution</h2>")
        parts.append(_bar_rows(list(llm["rating_distribution"].items()), fmt=str))

    steps = ev.get("llm_step_validation", {})
    if steps.get("n"):
        parts.append("<h2>LLM step-by-step CoT validation</h2><div class='grid'>")
        parts.append(_kpi("all steps OK", f'{(steps.get("all_steps_ok_rate") or 0)*100:.0f}%'))
        parts.append(_kpi("STEP1", f'{(steps.get("step1_ok_rate") or 0)*100:.0f}%'))
        parts.append(_kpi("STEP2", f'{(steps.get("step2_ok_rate") or 0)*100:.0f}%'))
        parts.append(_kpi("STEP3", f'{(steps.get("step3_ok_rate") or 0)*100:.0f}%'))
        parts.append(_kpi("STEP4", f'{(steps.get("step4_ok_rate") or 0)*100:.0f}%'))
        parts.append("</div>")

    improve = ev.get("llm_prompt_improvement", {})
    if improve.get("n"):
        parts.append("<h2>Prompt improvement (structure)</h2><div class='grid'>")
        parts.append(_kpi("v2 structure", improve.get("v2_structure_score", "-")))
        parts.append(_kpi("v1 structure", improve.get("v1_structure_score", "-")))
        parts.append(_kpi("lift (v2−v1)", improve.get("structure_lift", "-")))
        parts.append("</div>")
        parts.append(
            f'<p class="sub">Prompt version <code>{html.escape(str(improve.get("current_prompt_version","")))}</code> '
            f'&middot; explain model <code>{html.escape(config.OLLAMA_MODEL)}</code></p>'
        )

    # Drift
    if drift:
        parts.append("<h2>Model &amp; data drift (PSI)</h2><div class='grid'>")
        for key, title in [("predicted_category_psi", "category PSI"),
                           ("anomaly_score_psi", "score PSI")]:
            d = drift.get(key, {})
            band = d.get("band", "n/a")
            parts.append(
                f'<div class="card"><div class="kpi">{d.get("psi","-")}</div>'
                f'<div class="label">{title}</div>'
                f'<div style="margin-top:8px"><span class="badge {band}">{band}</span></div></div>')
        parts.append("</div>")

    parts.append('<p class="foot">Synthetic data only &middot; educational simulation.</p>')
    return "\n".join(parts)


def write(metrics: dict) -> Path:
    config.ensure_dirs()
    config.ANALYTICS_HTML.write_text(render(metrics))
    return config.ANALYTICS_HTML
