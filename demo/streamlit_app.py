"""InsightIQ full dashboard UI — calls the FastAPI backend for all data."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

API = "http://localhost:8000"


def get(endpoint: str, default=None):
    try:
        r = requests.get(f"{API}{endpoint}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        st.warning(f"API call failed for `{endpoint}`: {exc}")
        return default


def df(endpoint: str) -> pd.DataFrame:
    data = get(endpoint, default=[])
    return pd.DataFrame(data) if data else pd.DataFrame()


def _ensure_artifacts() -> None:
    health = get("/health")
    if health is None:
        st.error("❌ API is not running. Start it with: `python main.py`")
        st.stop()
    kpis = get("/metrics/summary")
    if not kpis:
        with st.spinner("⚙️ First run — building pipeline artifacts (~30s)..."):
            try:
                from scripts.generate_synthetic_datasets import main as gen_synthetic
                from insightiq.pipeline import run_pipeline
                gen_synthetic()
                run_pipeline()
                st.success("✅ Pipeline complete. Reloading...")
                st.rerun()
            except Exception as exc:
                st.error(f"Pipeline failed: {exc}")
                st.stop()


_ensure_artifacts()

st.set_page_config(page_title="InsightIQ", layout="wide", page_icon="🧠")

st.sidebar.title("🧠 InsightIQ")
st.sidebar.caption("AI Decision Intelligence Platform")
page = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Decision Summary",
        "📊 KPIs & Funnel",
        "🛒 Tableau Extract",
        "⭐ Review Intelligence",
        "🔬 Experiments",
        "🚨 Anomalies",
        "📈 Forecast",
        "👥 User Segments",
        "🚀 Release Impact",
        "🔍 Root Cause",
        "🤖 AI Agent Run",
        "📋 PRD Compliance",
    ],
)


def action_color(action: str) -> str:
    return {"investigate": "🔴", "iterate": "🟡", "launch": "🟢", "rollback": "⚫"}.get(
        action.lower(), "⚪"
    )


# ── pages ─────────────────────────────────────────────────────────────────────

if page == "🏠 Decision Summary":
    st.title("Decision Summary")
    payload = get("/decision-intelligence/run", default={})
    if not payload:
        st.info("No decision run data available.")
        st.stop()

    recommendation = payload["recommendation"]
    action = recommendation["action"].upper()
    color = action_color(recommendation["action"])
    st.markdown(f"## {color} Final Decision: `{action}`")
    st.markdown(f"> {recommendation['rationale']}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Decision", action)
    c2.metric("Confidence", recommendation["confidence"])
    c3.metric("Evidence Coverage", payload["evaluation"]["evidence_coverage"])
    c4.metric("Agents Run", payload["evaluation"]["agent_count"])
    c5.metric("Evidence Items", payload["evaluation"]["evidence_item_count"])

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚠️ Risks")
        for r in recommendation["risks"]:
            st.markdown(f"- {r}")
    with col2:
        st.subheader("✅ Next Actions")
        for a in recommendation["next_actions"]:
            st.markdown(f"- {a}")

    st.divider()
    st.subheader("🤖 LLM Memo")
    llm = payload.get("llm", {})
    st.info(llm.get("text", "No LLM memo available."))
    st.caption(
        f"Model: {llm.get('model')} | Remote LLM: {llm.get('used_remote_llm')} | LangGraph: {payload.get('used_langgraph')}"
    )

elif page == "📊 KPIs & Funnel":
    st.title("KPIs & Funnel")
    kpis = get("/metrics/summary", default={})
    if kpis:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Completed Revenue", f"USD {kpis['completed_revenue']:,.0f}")
        c2.metric("Avg Order Value", f"USD {kpis['average_order_value']:,.2f}")
        c3.metric("Purchase Conversion", f"{kpis['purchase_conversion']:.1%}")
        c4.metric("Cancellation Rate", f"{kpis['cancellation_rate']:.1%}")

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Cart Rate", f"{kpis['cart_rate']:.1%}")
        c6.metric("Avg Review Rating", kpis["avg_review_rating"])
        c7.metric("Total Orders", f"{kpis['total_orders']:,}")
        c8.metric("Total Users", f"{kpis['total_users']:,}")

    st.divider()
    st.subheader("Conversion Funnel")
    funnel = df("/metrics/funnel")
    if not funnel.empty:
        st.bar_chart(funnel.set_index("step")["users"])
        st.dataframe(funnel, use_container_width=True)

    st.subheader("Monthly Revenue")
    monthly = df("/metrics/monthly-revenue")
    if not monthly.empty:
        monthly["revenue"] = pd.to_numeric(monthly["revenue"], errors="coerce")
        st.line_chart(monthly.set_index("month")["revenue"])
        st.dataframe(monthly, use_container_width=True)

elif page == "🛒 Tableau Extract":
    st.title("Tableau Dashboard Extract")
    st.caption("Revenue, orders, units, and review ratings by category and brand.")
    data = df("/metrics/tableau")
    if not data.empty:
        category = st.multiselect("Filter by category", sorted(data["category"].unique()), default=[])
        if category:
            data = data[data["category"].isin(category)]
        st.dataframe(data, use_container_width=True)
        st.subheader("Gross Revenue by Category")
        data["gross_item_revenue"] = pd.to_numeric(data["gross_item_revenue"], errors="coerce")
        rev = data.groupby("category")["gross_item_revenue"].sum().sort_values(ascending=False)
        st.bar_chart(rev)

elif page == "⭐ Review Intelligence":
    st.title("Review Intelligence")
    st.caption("Sentiment scoring + NMF topic modeling across category, brand, and topic.")
    data = df("/reviews/intelligence")
    if not data.empty:
        col1, col2 = st.columns(2)
        sentiment_filter = col1.multiselect(
            "Sentiment", ["positive", "neutral", "negative"], default=["negative"]
        )
        category_filter = col2.multiselect("Category", sorted(data["category"].unique()), default=[])
        filtered = data.copy()
        if sentiment_filter:
            filtered = filtered[filtered["sentiment"].isin(sentiment_filter)]
        if category_filter:
            filtered = filtered[filtered["category"].isin(category_filter)]
        data["reviews"] = pd.to_numeric(data["reviews"], errors="coerce")
        filtered["reviews"] = pd.to_numeric(filtered["reviews"], errors="coerce")
        st.dataframe(filtered.sort_values("reviews", ascending=False), use_container_width=True)
        st.subheader("Review Count by Sentiment")
        st.bar_chart(data.groupby("sentiment")["reviews"].sum())

elif page == "🔬 Experiments":
    st.title("Experiment Decisions")
    data = df("/experiments/decisions")
    if not data.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Ship or Expand", int((data["rollout_recommendation"] == "ship_or_expand").sum()))
        c2.metric("Continue / Segment", int((data["rollout_recommendation"] == "continue_test_or_segment").sum()))
        c3.metric("Rollback / Redesign", int((data["rollout_recommendation"] == "rollback_or_redesign").sum()))
        st.dataframe(data, use_container_width=True)

elif page == "🚨 Anomalies":
    st.title("Anomaly Detection")
    st.caption("IsolationForest on daily revenue, orders, and cancellation rate.")
    data = df("/anomalies")
    if not data.empty:
        data["is_anomaly"] = data["is_anomaly"].map(lambda x: str(x).lower() in ("true", "1"))
        anomalies_only = st.checkbox("Show anomalies only", value=False)
        display = data[data["is_anomaly"]] if anomalies_only else data
        st.metric("Anomalous Days", int(data["is_anomaly"].sum()))
        st.dataframe(display, use_container_width=True)
        st.subheader("Daily Revenue")
        data["revenue"] = pd.to_numeric(data["revenue"], errors="coerce")
        st.line_chart(data.set_index("order_day")["revenue"])

elif page == "📈 Forecast":
    st.title("Revenue Forecast")
    st.caption("14-day projection using 28-day trailing mean + trend.")
    data = df("/forecast")
    if not data.empty:
        data["forecast_revenue"] = pd.to_numeric(data["forecast_revenue"], errors="coerce")
        st.line_chart(data.set_index("forecast_day")["forecast_revenue"])
        st.dataframe(data, use_container_width=True)

elif page == "👥 User Segments":
    st.title("User Segments")
    st.caption("KMeans clustering (4 segments) on spend, orders, events, and cancellation rate.")
    profiles = df("/segments/profiles")
    if not profiles.empty:
        profiles["avg_spend"] = pd.to_numeric(profiles["avg_spend"], errors="coerce")
        profiles["avg_orders"] = pd.to_numeric(profiles["avg_orders"], errors="coerce")
        st.dataframe(profiles, use_container_width=True)
        st.subheader("Avg Spend by Segment")
        st.bar_chart(profiles.set_index("segment")["avg_spend"])
        st.subheader("Avg Orders by Segment")
        st.bar_chart(profiles.set_index("segment")["avg_orders"])

elif page == "🚀 Release Impact":
    st.title("Release Impact")
    st.caption("Releases correlated with anomaly dates and engineering incidents.")
    data = df("/release/impact")
    if not data.empty:
        c1, c2 = st.columns(2)
        c1.metric("Risky Releases", int((data["risk_note"] == "investigate").sum()))
        c2.metric("Low Risk Releases", int((data["risk_note"] == "low_risk").sum()))
        risk_filter = st.selectbox("Filter by risk", ["all", "investigate", "low_risk"], index=0)
        display = data if risk_filter == "all" else data[data["risk_note"] == risk_filter]
        data["nearby_anomalies"] = pd.to_numeric(data["nearby_anomalies"], errors="coerce")
        st.dataframe(display.sort_values("nearby_anomalies", ascending=False), use_container_width=True)

elif page == "🔍 Root Cause":
    st.title("Root Cause Hypotheses")
    data = df("/root-cause/hypotheses")
    if not data.empty:
        for _, row in data.iterrows():
            with st.expander(f"#{int(row['rank'])} — {row['hypothesis']} (confidence: {row['confidence']})"):
                st.markdown(f"**Evidence:** {row['evidence']}")
                st.markdown(f"**Recommended Action:** {row['recommended_action']}")

elif page == "🤖 AI Agent Run":
    st.title("AI Agent Run — LangGraph Decision Intelligence")
    payload = get("/decision-intelligence/run", default={})
    if not payload:
        st.info("No agent run data available.")
        st.stop()

    recommendation = payload["recommendation"]
    st.caption(
        f"LangGraph used: {payload.get('used_langgraph')} | Remote LLM: {payload.get('llm', {}).get('used_remote_llm')}"
    )
    st.subheader("Decision Question")
    st.write(payload["question"]["question"])

    st.subheader("Agent Findings")
    for finding in recommendation["findings"]:
        with st.expander(f"🤖 {finding['agent']} — {finding['finding'][:80]}..."):
            st.write(finding["finding"])
            st.write(f"Confidence: {finding['confidence']}")
            for item in finding["evidence"][:5]:
                st.markdown(
                    f"- **{item['source']} / {item['title']}** (conf={item['confidence']}): {item['summary'][:300]}"
                )

    st.subheader("Evaluation Metrics")
    eval_data = payload["evaluation"]
    cols = st.columns(len(eval_data))
    for col, (k, v) in zip(cols, eval_data.items()):
        col.metric(k.replace("_", " ").title(), v)

    st.subheader("Full JSON Payload")
    st.json(payload)

elif page == "📋 PRD Compliance":
    st.title("PRD Compliance Matrix")
    data = df("/prd/compliance")
    if not data.empty:
        complete = int((data["status"] == "complete").sum())
        st.metric("Requirements Met", f"{complete}/{len(data)}")
        st.dataframe(data, use_container_width=True)
