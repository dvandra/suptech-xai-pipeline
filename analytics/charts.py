"""Pure-SVG chart rendering for LLM / RAG / audit metrics.

No matplotlib/plotly required — SVGs embed in the HTML report, Streamlit
(via components), and GitHub Markdown so reviewers see graphs without
running a server.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import config

CHARTS_DIR = config.REPORTS_DIR / "charts"
SAMPLE_CHARTS_DIR = config.ROOT / "docs" / "sample_reports" / "charts"


def _svg_bar(
    title: str,
    items: list[tuple[str, float]],
    *,
    width: int = 640,
    height: int = 320,
    ymax: float | None = None,
    value_fmt: str = "{:.2f}",
    color: str = "#38bdf8",
) -> str:
    pad_l, pad_r, pad_t, pad_b = 56, 24, 40, 56
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    if not items:
        items = [("n/a", 0.0)]
    ymax = ymax if ymax is not None else max((v for _, v in items), default=1.0) or 1.0
    n = len(items)
    gap = 8
    bar_w = max(12, (plot_w - gap * (n + 1)) / n)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">',
        f'<rect width="100%" height="100%" fill="#0f172a"/>',
        f'<text x="{pad_l}" y="24" fill="#e2e8f0" font-size="15" '
        f'font-family="system-ui,sans-serif" font-weight="600">{html.escape(title)}</text>',
        # axis
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t+plot_h}" '
        f'stroke="#475569" stroke-width="1"/>',
        f'<line x1="{pad_l}" y1="{pad_t+plot_h}" x2="{pad_l+plot_w}" y2="{pad_t+plot_h}" '
        f'stroke="#475569" stroke-width="1"/>',
    ]
    # y ticks
    for frac in (0.0, 0.5, 1.0):
        y = pad_t + plot_h * (1 - frac)
        val = ymax * frac
        parts.append(
            f'<line x1="{pad_l}" y1="{y}" x2="{pad_l+plot_w}" y2="{y}" '
            f'stroke="#1e293b" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{pad_l-8}" y="{y+4}" fill="#94a3b8" font-size="11" '
            f'text-anchor="end" font-family="system-ui,sans-serif">'
            f'{value_fmt.format(val)}</text>'
        )

    for i, (label, value) in enumerate(items):
        x = pad_l + gap + i * (bar_w + gap)
        h = (value / ymax) * plot_h if ymax else 0
        y = pad_t + plot_h - h
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
            f'rx="4" fill="{color}"/>'
        )
        parts.append(
            f'<text x="{x + bar_w/2:.1f}" y="{y - 6:.1f}" fill="#e2e8f0" font-size="11" '
            f'text-anchor="middle" font-family="system-ui,sans-serif">'
            f'{value_fmt.format(value)}</text>'
        )
        # label (truncate)
        lab = label if len(label) <= 12 else label[:11] + "…"
        parts.append(
            f'<text x="{x + bar_w/2:.1f}" y="{pad_t+plot_h+18}" fill="#94a3b8" '
            f'font-size="11" text-anchor="middle" font-family="system-ui,sans-serif">'
            f'{html.escape(lab)}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def _svg_line(
    title: str,
    points: list[tuple[float, float]],
    *,
    width: int = 640,
    height: int = 300,
    xlab: str = "x",
    ylab: str = "y",
) -> str:
    pad_l, pad_r, pad_t, pad_b = 56, 24, 40, 48
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    if len(points) < 2:
        points = [(0.0, 0.0), (1.0, 0.0)]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if xmax == xmin:
        xmax = xmin + 1
    if ymax == ymin:
        ymax = ymin + 1

    def px(x: float) -> float:
        return pad_l + (x - xmin) / (xmax - xmin) * plot_w

    def py(y: float) -> float:
        return pad_t + (1 - (y - ymin) / (ymax - ymin)) * plot_h

    poly = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in points)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">',
        f'<rect width="100%" height="100%" fill="#0f172a"/>',
        f'<text x="{pad_l}" y="24" fill="#e2e8f0" font-size="15" '
        f'font-family="system-ui,sans-serif" font-weight="600">{html.escape(title)}</text>',
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t+plot_h}" stroke="#475569"/>',
        f'<line x1="{pad_l}" y1="{pad_t+plot_h}" x2="{pad_l+plot_w}" y2="{pad_t+plot_h}" stroke="#475569"/>',
        f'<polyline fill="none" stroke="#38bdf8" stroke-width="2.5" points="{poly}"/>',
    ]
    for x, y in points[:: max(1, len(points) // 8)]:
        parts.append(
            f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="3.5" fill="#fbbf24"/>'
        )
    parts.append(
        f'<text x="{pad_l+plot_w/2}" y="{height-10}" fill="#94a3b8" font-size="11" '
        f'text-anchor="middle" font-family="system-ui,sans-serif">{html.escape(xlab)}</text>'
    )
    parts.append(
        f'<text x="14" y="{pad_t+plot_h/2}" fill="#94a3b8" font-size="11" '
        f'transform="rotate(-90 14,{pad_t+plot_h/2})" '
        f'font-family="system-ui,sans-serif">{html.escape(ylab)}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def _svg_grouped_bars(
    title: str,
    categories: list[str],
    series: dict[str, list[float]],
    *,
    width: int = 720,
    height: int = 340,
    colors: list[str] | None = None,
) -> str:
    colors = colors or ["#38bdf8", "#4ade80", "#fbbf24", "#f87171", "#c084fc"]
    pad_l, pad_r, pad_t, pad_b = 56, 24, 48, 64
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    keys = list(series.keys())
    n_cat = max(len(categories), 1)
    n_ser = max(len(keys), 1)
    ymax = max((v for vals in series.values() for v in vals), default=1.0) or 1.0
    group_w = plot_w / n_cat
    bar_w = max(6, (group_w * 0.7) / n_ser)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">',
        f'<rect width="100%" height="100%" fill="#0f172a"/>',
        f'<text x="{pad_l}" y="24" fill="#e2e8f0" font-size="15" '
        f'font-family="system-ui,sans-serif" font-weight="600">{html.escape(title)}</text>',
        f'<line x1="{pad_l}" y1="{pad_t+plot_h}" x2="{pad_l+plot_w}" y2="{pad_t+plot_h}" stroke="#475569"/>',
    ]
    # legend
    lx = pad_l
    for i, key in enumerate(keys):
        c = colors[i % len(colors)]
        parts.append(f'<rect x="{lx}" y="30" width="12" height="12" rx="2" fill="{c}"/>')
        parts.append(
            f'<text x="{lx+16}" y="40" fill="#94a3b8" font-size="11" '
            f'font-family="system-ui,sans-serif">{html.escape(key)}</text>'
        )
        lx += 90

    for ci, cat in enumerate(categories):
        gx = pad_l + ci * group_w + group_w * 0.15
        for si, key in enumerate(keys):
            vals = series[key]
            value = vals[ci] if ci < len(vals) else 0.0
            h = (value / ymax) * plot_h
            x = gx + si * bar_w
            y = pad_t + plot_h - h
            c = colors[si % len(colors)]
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w-2:.1f}" height="{h:.1f}" '
                f'rx="3" fill="{c}"/>'
            )
        parts.append(
            f'<text x="{pad_l + ci * group_w + group_w/2:.1f}" y="{pad_t+plot_h+18}" '
            f'fill="#94a3b8" font-size="11" text-anchor="middle" '
            f'font-family="system-ui,sans-serif">{html.escape(cat)}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def build_chart_svgs(
    metrics: dict | None = None,
    rag: dict | None = None,
    audit: dict | None = None,
) -> dict[str, str]:
    """Return mapping of chart filename → SVG string."""
    if metrics is None and config.METRICS_JSON.exists():
        metrics = json.loads(config.METRICS_JSON.read_text())
    if rag is None and config.RAG_RESULTS_JSON.exists():
        rag = json.loads(config.RAG_RESULTS_JSON.read_text())
    if audit is None and config.AUDIT_SUMMARY_JSON.exists():
        audit = json.loads(config.AUDIT_SUMMARY_JSON.read_text())

    metrics = metrics or {}
    rag = rag or {}
    audit = audit or {}
    ev = metrics.get("evaluation", {})
    charts: dict[str, str] = {}

    # LLM step validation
    steps = ev.get("llm_step_validation") or {}
    if steps.get("n"):
        items = [
            ("STEP1", float(steps.get("step1_ok_rate") or 0)),
            ("STEP2", float(steps.get("step2_ok_rate") or 0)),
            ("STEP3", float(steps.get("step3_ok_rate") or 0)),
            ("STEP4", float(steps.get("step4_ok_rate") or 0)),
            ("ALL", float(steps.get("all_steps_ok_rate") or 0)),
        ]
        charts["llm_step_pass_rates.svg"] = _svg_bar(
            "LLM CoT step pass rates", items, ymax=1.0, value_fmt="{:.0%}", color="#4ade80"
        )

    llm = ev.get("llm_output") or {}
    if llm.get("rating_distribution"):
        items = [(k, float(v)) for k, v in llm["rating_distribution"].items()]
        charts["llm_risk_rating_distribution.svg"] = _svg_bar(
            "LLM risk-rating distribution", items, value_fmt="{:.0f}", color="#38bdf8"
        )

    judge = ev.get("llm_as_judge") or {}
    if judge.get("score_distribution"):
        dist = judge["score_distribution"]
        items = [(str(k), float(dist[k])) for k in sorted(dist, key=lambda x: int(x))]
        charts["llm_judge_score_distribution.svg"] = _svg_bar(
            f"LLM-as-judge scores (avg={judge.get('avg_score')})",
            items,
            value_fmt="{:.0f}",
            color="#fbbf24",
        )

    sweep = ev.get("threshold_sweep") or {}
    if sweep.get("curve"):
        pts = [(float(p["sigma"]), float(p["f1"])) for p in sweep["curve"]]
        charts["detector_threshold_f1.svg"] = _svg_line(
            "Detector threshold sweep (F1 vs sigma)",
            pts,
            xlab="sigma",
            ylab="F1",
        )

    # RAG by retriever / model / track
    summary = rag.get("summary") or {}
    by_ret = summary.get("by_retriever") or {}
    if by_ret:
        cats = list(by_ret.keys())
        series = {
            "hit@k": [float(by_ret[c].get("hit_at_k") or 0) for c in cats],
            "citation": [float(by_ret[c].get("citation_rate") or 0) for c in cats],
            "faithfulness": [float(by_ret[c].get("faithfulness_proxy") or 0) for c in cats],
        }
        charts["rag_by_retriever.svg"] = _svg_grouped_bars(
            "RAG metrics by retriever", cats, series
        )

    by_model = summary.get("by_model") or {}
    if by_model:
        items = [
            (m, float(v.get("faithfulness_proxy") or 0)) for m, v in by_model.items()
        ]
        charts["rag_faithfulness_by_model.svg"] = _svg_bar(
            "RAG faithfulness proxy by model",
            items,
            ymax=1.0,
            value_fmt="{:.0%}",
            color="#c084fc",
        )

    by_track = summary.get("by_track") or {}
    if by_track:
        cats = list(by_track.keys())
        series = {
            "hit@k": [float(by_track[c].get("hit_at_k") or 0) for c in cats],
            "recall@k": [float(by_track[c].get("recall_at_k") or 0) for c in cats],
            "faithfulness": [float(by_track[c].get("faithfulness_proxy") or 0) for c in cats],
        }
        charts["rag_by_track.svg"] = _svg_grouped_bars(
            "RAG metrics by question track", cats, series
        )

    # Audit by pipeline
    by_pipe = audit.get("by_pipeline") or {}
    if by_pipe:
        cats = list(by_pipe.keys())
        series = {
            "ok": [float(by_pipe[c].get("ok") or 0) for c in cats],
            "failed": [float(by_pipe[c].get("failed") or 0) for c in cats],
        }
        charts["audit_by_pipeline.svg"] = _svg_grouped_bars(
            "Audit events by pipeline (ok vs failed)",
            cats,
            series,
            colors=["#4ade80", "#f87171"],
        )

    return charts


def write_charts(
    metrics: dict | None = None,
    rag: dict | None = None,
    audit: dict | None = None,
    *,
    also_sample: bool = True,
) -> list[Path]:
    """Write SVG charts under data/reports/charts/ (and docs sample copy)."""
    config.ensure_dirs()
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    charts = build_chart_svgs(metrics=metrics, rag=rag, audit=audit)
    paths: list[Path] = []
    for name, svg in charts.items():
        p = CHARTS_DIR / name
        p.write_text(svg)
        paths.append(p)
        if also_sample:
            SAMPLE_CHARTS_DIR.mkdir(parents=True, exist_ok=True)
            (SAMPLE_CHARTS_DIR / name).write_text(svg)
    # index markdown for GitHub gallery
    if also_sample and charts:
        lines = [
            "# Chart gallery — LLM, RAG & audit",
            "",
            "Auto-generated SVG charts from a local pipeline run. Reviewers can "
            "view these on GitHub without starting Streamlit.",
            "",
        ]
        for name in charts:
            title = name.replace(".svg", "").replace("_", " ").title()
            lines += [f"## {title}", "", f"![{title}]({name})", ""]
        (SAMPLE_CHARTS_DIR / "README.md").write_text("\n".join(lines))
    return paths


def run() -> list[Path]:
    paths = write_charts()
    print(f"[charts] wrote {len(paths)} SVGs -> {CHARTS_DIR}")
    if SAMPLE_CHARTS_DIR.exists():
        print(f"[charts] sample gallery -> {SAMPLE_CHARTS_DIR}")
    return paths


if __name__ == "__main__":
    run()
