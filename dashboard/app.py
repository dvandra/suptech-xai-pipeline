"""Streamlit analytics dashboard for the SupTech-XAI pipeline.

Interactive views for supervisory KPIs, LLM evaluation, RAG comparison,
drift, and the explainability audit trail — with charts reviewers care about.

Run:
    streamlit run dashboard/app.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402
from analytics.charts import CHARTS_DIR, build_chart_svgs, write_charts  # noqa: E402


@st.cache_data(show_spinner=False)
def load_json(path: str) -> dict | None:
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text())


def _show_svg(svg: str, *, height: int = 360):
    st.components.v1.html(svg, height=height, scrolling=False)


def _metric_row(items: list[tuple[str, object]]):
    cols = st.columns(len(items))
    for c, (label, value) in zip(cols, items):
        c.metric(label, value)


st.set_page_config(
    page_title="SupTech-XAI Analytics",
    layout="wide",
    page_icon="📊",
)
st.title("SupTech-XAI — Live Analytics Dashboard")
st.caption(
    "Supervisory KPIs · LLM evaluation · RAG comparison · Audit trail · "
    "Synthetic data only · educational simulation."
)

metrics = load_json(str(config.METRICS_JSON))
rag = load_json(str(config.RAG_RESULTS_JSON))
audit = load_json(str(config.AUDIT_SUMMARY_JSON))

if metrics is None:
    st.error("No pipeline output found. Run `python run_demo.py` first.")
    st.stop()

col_a, col_b = st.columns([3, 1])
with col_b:
    if st.button("Regenerate chart SVGs", use_container_width=True):
        write_charts(metrics=metrics, rag=rag, audit=audit)
        st.success(f"Wrote charts to {CHARTS_DIR}")
        st.cache_data.clear()

svgs = build_chart_svgs(metrics=metrics, rag=rag, audit=audit)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Supervisory",
        "LLM / XAI",
        "RAG comparison",
        "Drift",
        "Audit trail",
    ]
)

sup = metrics.get("supervisory", {})
ev = metrics.get("evaluation", {})
drift = metrics.get("drift", {})

with tab1:
    t = sup.get("totals", {})
    _metric_row(
        [
            ("Observations", t.get("observations", 0)),
            ("Anomalies", t.get("anomalies", 0)),
            ("Anomaly rate", f"{t.get('anomaly_rate', 0) * 100:.1f}%"),
            ("Flagged value", f"{t.get('flagged_value', 0):,.0f}"),
        ]
    )
    gov = sup.get("governance", {})
    if gov:
        st.metric("FMR rejection rate", f"{gov.get('rejection_rate', 0) * 100:.1f}%")

    left, right = st.columns(2)
    with left:
        if sup.get("by_ref_area"):
            st.subheader("Flagged value by jurisdiction")
            st.bar_chart(
                {r["ref_area"]: r["flagged_value"] for r in sup["by_ref_area"]}
            )
    with right:
        if "detector_threshold_f1.svg" in svgs:
            st.subheader("Detector F1 vs threshold")
            _show_svg(svgs["detector_threshold_f1.svg"])
        elif ev.get("threshold_sweep", {}).get("curve"):
            st.subheader("Threshold sweep (F1 vs sigma)")
            st.line_chart(
                {p["sigma"]: p["f1"] for p in ev["threshold_sweep"]["curve"]}
            )

    if sup.get("by_asset_class"):
        st.subheader("By asset class")
        st.dataframe(sup["by_asset_class"], use_container_width=True)
    if sup.get("top_institutions"):
        st.subheader("Top flagged institutions")
        st.dataframe(sup["top_institutions"], use_container_width=True)

with tab2:
    det = ev.get("detection", {})
    _metric_row(
        [
            ("Precision", det.get("precision", 0)),
            ("Recall", det.get("recall", 0)),
            ("F1", det.get("f1", 0)),
            ("Accuracy", det.get("accuracy", 0)),
        ]
    )

    llm = ev.get("llm_output", {})
    judge = ev.get("llm_as_judge", {})
    steps = ev.get("llm_step_validation", {})
    if llm.get("n"):
        _metric_row(
            [
                (
                    "Output validity",
                    f"{(llm.get('output_validity_rate') or 0) * 100:.0f}%",
                ),
                (
                    "Faithfulness",
                    f"{(llm.get('faithfulness_recall') or 0) * 100:.0f}%"
                    if llm.get("faithfulness_recall") is not None
                    else "n/a",
                ),
                (
                    "Judge avg",
                    f"{judge.get('avg_score', 'n/a')}/5",
                ),
                (
                    "CoT all-steps OK",
                    f"{(steps.get('all_steps_ok_rate') or 0) * 100:.0f}%",
                ),
            ]
        )

    c1, c2 = st.columns(2)
    with c1:
        if "llm_step_pass_rates.svg" in svgs:
            _show_svg(svgs["llm_step_pass_rates.svg"])
        if "llm_risk_rating_distribution.svg" in svgs:
            _show_svg(svgs["llm_risk_rating_distribution.svg"])
    with c2:
        if "llm_judge_score_distribution.svg" in svgs:
            _show_svg(svgs["llm_judge_score_distribution.svg"])
        improve = ev.get("llm_prompt_improvement") or {}
        if improve.get("n"):
            st.subheader("Prompt structure improvement")
            _metric_row(
                [
                    ("v2 structure", improve.get("v2_structure_score")),
                    ("v1 structure", improve.get("v1_structure_score")),
                    ("Lift", improve.get("structure_lift")),
                ]
            )

    cm = det.get("confusion_matrix", {})
    if cm:
        st.subheader("Detector confusion matrix")
        st.table(
            {
                "": ["actual +", "actual -"],
                "predicted +": [cm["tp"], cm["fp"]],
                "predicted -": [cm["fn"], cm["tn"]],
            }
        )

with tab3:
    if not rag:
        st.warning(
            "No RAG results yet. Run `make rag` or `python run_demo.py --with-rag`."
        )
    else:
        overall = (rag.get("summary") or {}).get("overall") or {}
        cfg = rag.get("config") or {}
        st.caption(
            f"Retrievers: {', '.join(cfg.get('retrievers') or [])} · "
            f"Models: {', '.join(cfg.get('models') or [])} · "
            f"n={overall.get('n')}"
        )
        _metric_row(
            [
                ("Hit@k", overall.get("hit_at_k")),
                ("Recall@k", overall.get("recall_at_k")),
                ("Citation", overall.get("citation_rate")),
                ("Faithfulness", overall.get("faithfulness_proxy")),
            ]
        )
        c1, c2 = st.columns(2)
        with c1:
            if "rag_by_retriever.svg" in svgs:
                _show_svg(svgs["rag_by_retriever.svg"], height=380)
            if "rag_by_track.svg" in svgs:
                _show_svg(svgs["rag_by_track.svg"], height=380)
        with c2:
            if "rag_faithfulness_by_model.svg" in svgs:
                _show_svg(svgs["rag_faithfulness_by_model.svg"])
            by_ret = (rag.get("summary") or {}).get("by_retriever") or {}
            if by_ret:
                st.subheader("Retriever scorecard")
                st.dataframe(by_ret, use_container_width=True)

with tab4:
    if not drift:
        st.write("No drift metrics available.")
    else:
        st.write(drift.get("note", ""))
        cols = st.columns(2)
        for i, (key, title) in enumerate(
            [
                ("predicted_category_psi", "Predicted-category PSI"),
                ("anomaly_score_psi", "Anomaly-score PSI"),
            ]
        ):
            d = drift.get(key, {})
            with cols[i]:
                st.metric(title, d.get("psi", "-"), help=f"band: {d.get('band')}")
                if d.get("breakdown"):
                    st.dataframe(d["breakdown"], use_container_width=True)

with tab5:
    if not audit:
        st.warning("No audit summary yet. Run `make audit`.")
    else:
        _metric_row(
            [
                ("Events", audit.get("n_events")),
                ("Passed", audit.get("n_ok")),
                ("Failed", audit.get("n_failed")),
                ("Pass rate", audit.get("pass_rate")),
            ]
        )
        if "audit_by_pipeline.svg" in svgs:
            _show_svg(svgs["audit_by_pipeline.svg"])
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("By pipeline")
            st.dataframe(audit.get("by_pipeline") or {}, use_container_width=True)
        with c2:
            st.subheader("By stage")
            st.dataframe(audit.get("by_stage") or {}, use_container_width=True)
        fails = audit.get("failures_sample") or []
        if fails:
            st.subheader("Failure sample")
            st.dataframe(fails, use_container_width=True)

st.divider()
st.markdown(
    f"Static chart gallery (for GitHub reviewers): "
    f"`docs/sample_reports/charts/` · live SVGs also in `{CHARTS_DIR}`"
)
