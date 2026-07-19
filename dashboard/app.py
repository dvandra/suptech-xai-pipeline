"""Streamlit analytics dashboard for the SupTech-XAI pipeline.

Reads the metrics produced by ``analytics/run_analytics.py`` (or recomputes
them on the fly) and presents supervisory analytics, AI-evaluation results and
drift monitoring interactively.

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


@st.cache_data(show_spinner=False)
def load_metrics() -> dict:
    if config.METRICS_JSON.exists():
        return json.loads(config.METRICS_JSON.read_text())
    from analytics.run_analytics import compute_all

    return compute_all()


st.set_page_config(page_title="SupTech-XAI Analytics", layout="wide")
st.title("SupTech-XAI — Supervisory Analytics & AI Evaluation")
st.caption(
    "Synthetic data only · educational simulation."
)

try:
    m = load_metrics()
except FileNotFoundError:
    st.error("No pipeline output found. Run `python run_demo.py` first.")
    st.stop()

sup = m.get("supervisory", {})
ev = m.get("evaluation", {})
drift = m.get("drift", {})

tab1, tab2, tab3 = st.tabs(
    ["Supervisory analytics", "AI evaluation", "Drift monitoring"]
)

with tab1:
    t = sup.get("totals", {})
    c = st.columns(4)
    c[0].metric("Observations", t.get("observations", 0))
    c[1].metric("Anomalies", t.get("anomalies", 0))
    c[2].metric("Anomaly rate", f"{t.get('anomaly_rate', 0) * 100:.1f}%")
    c[3].metric("Flagged value", f"{t.get('flagged_value', 0):,.0f}")

    gov = sup.get("governance", {})
    if gov:
        st.metric("FMR rejection rate", f"{gov.get('rejection_rate', 0) * 100:.1f}%")

    if sup.get("by_ref_area"):
        st.subheader("Flagged value by jurisdiction")
        st.bar_chart(
            {r["ref_area"]: r["flagged_value"] for r in sup["by_ref_area"]}
        )
    if sup.get("by_asset_class"):
        st.subheader("By asset class")
        st.dataframe(sup["by_asset_class"], use_container_width=True)
    if sup.get("top_institutions"):
        st.subheader("Top flagged institutions")
        st.dataframe(sup["top_institutions"], use_container_width=True)

with tab2:
    det = ev.get("detection", {})
    c = st.columns(4)
    c[0].metric("Precision", det.get("precision", 0))
    c[1].metric("Recall", det.get("recall", 0))
    c[2].metric("F1", det.get("f1", 0))
    c[3].metric("Accuracy", det.get("accuracy", 0))

    cm = det.get("confusion_matrix", {})
    if cm:
        st.subheader("Confusion matrix")
        st.table(
            {
                "": ["actual +", "actual -"],
                "predicted +": [cm["tp"], cm["fp"]],
                "predicted -": [cm["fn"], cm["tn"]],
            }
        )

    sweep = ev.get("threshold_sweep", {})
    if sweep.get("curve"):
        st.subheader("Threshold sweep (F1 vs sigma)")
        st.line_chart({p["sigma"]: p["f1"] for p in sweep["curve"]})
        b = sweep.get("best_operating_point", {})
        st.info(
            f"F1-optimal sigma = {b.get('sigma')} (F1={b.get('f1')}); "
            f"configured sigma = {sweep.get('current_sigma')}"
        )

    llm = ev.get("llm_output", {})
    if llm.get("n"):
        st.subheader("LLM explanation quality")
        c = st.columns(3)
        c[0].metric("Output validity", f"{(llm.get('output_validity_rate') or 0) * 100:.0f}%")
        fr = llm.get("faithfulness_recall")
        c[1].metric("Faithfulness recall", f"{fr * 100:.0f}%" if fr is not None else "n/a")
        judge = ev.get("llm_as_judge", {})
        if judge.get("avg_score") is not None:
            c[2].metric(f"LLM-as-judge ({judge.get('judge_engine')})", f"{judge['avg_score']}/5")
        if llm.get("rating_distribution"):
            st.bar_chart(llm["rating_distribution"])

with tab3:
    if not drift:
        st.write("No drift metrics available.")
    else:
        st.write(drift.get("note", ""))
        for key, title in [
            ("predicted_category_psi", "Predicted-category PSI"),
            ("anomaly_score_psi", "Anomaly-score PSI"),
        ]:
            d = drift.get(key, {})
            st.metric(title, d.get("psi", "-"), help=f"band: {d.get('band')}")
            if d.get("breakdown"):
                st.dataframe(d["breakdown"], use_container_width=True)
