"""Chat service — analyses real artifact data based on user question."""

from __future__ import annotations

import json
import statistics
from typing import Any

from .artifact_service import ArtifactService


class ChatService:
    def __init__(self, svc: ArtifactService) -> None:
        self.svc = svc

    # ── intent detection ──────────────────────────────────────────────────────
    def _intent(self, q: str) -> list[str]:
        q = q.lower()
        intents = []
        if any(w in q for w in ["revenue", "sales", "money", "gmv", "income"]):
            intents.append("revenue")
        if any(w in q for w in ["conversion", "funnel", "drop", "checkout"]):
            intents.append("funnel")
        if any(w in q for w in ["review", "sentiment", "complaint", "rating", "feedback", "customer"]):
            intents.append("reviews")
        if any(w in q for w in ["experiment", "ab test", "a/b", "test", "variant", "ship", "rollout"]):
            intents.append("experiments")
        if any(w in q for w in ["anomal", "spike", "drop", "unusual", "weird", "issue"]):
            intents.append("anomalies")
        if any(w in q for w in ["forecast", "predict", "future", "next", "projection"]):
            intents.append("forecast")
        if any(w in q for w in ["segment", "user", "cohort", "cluster", "group"]):
            intents.append("segments")
        if any(w in q for w in ["root cause", "why", "reason", "hypothesis", "cause"]):
            intents.append("root_cause")
        if any(w in q for w in ["kpi", "metric", "summary", "overview", "dashboard", "performance"]):
            intents.append("kpis")
        if any(w in q for w in ["release", "deploy", "launch", "incident", "impact"]):
            intents.append("release")
        if any(w in q for w in ["decision", "recommend", "should", "action", "next step"]):
            intents.append("decision")
        return intents or ["kpis"]

    # ── data loaders ──────────────────────────────────────────────────────────
    def _kpis(self) -> dict:
        try:
            return self.svc.read_json("kpi_summary.json")
        except Exception:
            return {}

    def _revenue(self) -> list[dict]:
        try:
            return self.svc.read_csv("monthly_revenue.csv")
        except Exception:
            return []

    def _funnel(self) -> list[dict]:
        try:
            return self.svc.read_csv("funnel_summary.csv")
        except Exception:
            return []

    def _reviews(self) -> list[dict]:
        try:
            return self.svc.read_csv("review_intelligence.csv", limit=500)
        except Exception:
            return []

    def _experiments(self) -> list[dict]:
        try:
            return self.svc.read_csv("experiment_decisions.csv")
        except Exception:
            return []

    def _anomalies(self) -> list[dict]:
        try:
            return self.svc.read_csv("anomalies.csv")
        except Exception:
            return []

    def _forecast(self) -> list[dict]:
        try:
            return self.svc.read_csv("forecast.csv")
        except Exception:
            return []

    def _segments(self) -> list[dict]:
        try:
            return self.svc.read_csv("segment_profiles.csv")
        except Exception:
            return []

    def _root_cause(self) -> list[dict]:
        try:
            return self.svc.read_csv("root_cause_hypotheses.csv")
        except Exception:
            return []

    def _decision_run(self) -> dict:
        try:
            return self.svc.read_json("decision_intelligence_run.json")
        except Exception:
            return {}

    def _release(self) -> list[dict]:
        try:
            return self.svc.read_csv("release_impact.csv")
        except Exception:
            return []

    # ── section builders ─────────────────────────────────────────────────────
    def _section_kpis(self) -> tuple[str, list]:
        k = self._kpis()
        if not k:
            return "", []
        rev = k.get("completed_revenue", 0)
        aov = k.get("average_order_value", 0)
        conv = k.get("purchase_conversion", 0)
        cancel = k.get("cancellation_rate", 0)
        rating = k.get("avg_review_rating", 0)
        orders = k.get("total_orders", 0)
        users = k.get("total_users", 0)

        md = f"""## 📊 KPI Summary

| Metric | Value |
|--------|-------|
| Total Revenue | ${rev:,.0f} |
| Avg Order Value | ${aov:,.2f} |
| Purchase Conversion | {conv:.1%} |
| Cancellation Rate | {cancel:.1%} |
| Avg Review Rating | {rating} / 5 |
| Total Orders | {orders:,} |
| Total Users | {users:,} |

"""
        chart = {
            "type": "bar",
            "title": "Key Metrics",
            "data": [
                {"name": "Conversion %", "value": round(conv * 100, 2)},
                {"name": "Cancellation %", "value": round(cancel * 100, 2)},
                {"name": "Avg Rating", "value": float(rating)},
            ],
        }
        return md, [chart]

    def _section_revenue(self) -> tuple[str, list]:
        rows = self._revenue()
        if not rows:
            return "", []
        recent = rows[-6:]
        revenues = [float(r["revenue"]) for r in recent]
        trend = "📈 upward" if revenues[-1] > revenues[0] else "📉 downward"
        peak = max(recent, key=lambda r: float(r["revenue"]))
        low = min(recent, key=lambda r: float(r["revenue"]))

        table = "\n".join(f"| {r['month']} | ${float(r['revenue']):,.0f} | {r['orders']} |" for r in recent)
        md = f"""## 💰 Revenue Analysis

Trend over last 6 months is **{trend}**.

| Month | Revenue | Orders |
|-------|---------|--------|
{table}

- **Peak month:** {peak['month']} at ${float(peak['revenue']):,.0f}
- **Lowest month:** {low['month']} at ${float(low['revenue']):,.0f}
- **Avg monthly revenue:** ${statistics.mean(revenues):,.0f}

"""
        chart = {
            "type": "line",
            "title": "Monthly Revenue",
            "data": [{"name": r["month"], "value": float(r["revenue"])} for r in rows[-12:]],
        }
        return md, [chart]

    def _section_funnel(self) -> tuple[str, list]:
        rows = self._funnel()
        if not rows:
            return "", []
        steps = [(r["step"], int(r["users"])) for r in rows]
        top = steps[0][1] if steps else 1
        table = "\n".join(f"| {s} | {u:,} | {u/top:.1%} |" for s, u in steps)
        # find biggest drop
        drops = [(steps[i][0], steps[i][1] - steps[i+1][1]) for i in range(len(steps)-1)]
        worst = max(drops, key=lambda x: x[1]) if drops else ("—", 0)

        md = f"""## 🔻 Conversion Funnel

| Step | Users | % of Top |
|------|-------|----------|
{table}

> ⚠️ **Biggest drop-off:** After **{worst[0]}** — {worst[1]:,} users lost

"""
        chart = {
            "type": "bar",
            "title": "Conversion Funnel",
            "data": [{"name": s, "value": u} for s, u in steps],
        }
        return md, [chart]

    def _section_reviews(self) -> tuple[str, list]:
        rows = self._reviews()
        if not rows:
            return "", []
        sentiment_counts: dict[str, int] = {}
        topic_counts: dict[str, int] = {}
        neg_topics: dict[str, int] = {}
        for r in rows:
            s = r.get("sentiment", "")
            t = r.get("topic", "")
            cnt = int(r.get("reviews", 0))
            sentiment_counts[s] = sentiment_counts.get(s, 0) + cnt
            topic_counts[t] = topic_counts.get(t, 0) + cnt
            if s == "negative":
                neg_topics[t] = neg_topics.get(t, 0) + cnt

        top_neg = sorted(neg_topics.items(), key=lambda x: x[1], reverse=True)[:5]
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        neg_table = "\n".join(f"| {t} | {c:,} |" for t, c in top_neg)
        topic_table = "\n".join(f"| {t} | {c:,} |" for t, c in top_topics)

        total = sum(sentiment_counts.values()) or 1
        md = f"""## ⭐ Review Intelligence

**Sentiment breakdown:**
- 🟢 Positive: {sentiment_counts.get('positive', 0):,} ({sentiment_counts.get('positive', 0)/total:.1%})
- 🟡 Neutral: {sentiment_counts.get('neutral', 0):,} ({sentiment_counts.get('neutral', 0)/total:.1%})
- 🔴 Negative: {sentiment_counts.get('negative', 0):,} ({sentiment_counts.get('negative', 0)/total:.1%})

**Top complaint topics:**

| Topic | Negative Reviews |
|-------|-----------------|
{neg_table}

**Top topics overall:**

| Topic | Reviews |
|-------|---------|
{topic_table}

"""
        chart = {
            "type": "pie",
            "title": "Sentiment Distribution",
            "data": [{"name": k, "value": v} for k, v in sentiment_counts.items()],
        }
        return md, [chart]

    def _section_experiments(self) -> tuple[str, list]:
        rows = self._experiments()
        if not rows:
            return "", []
        def _pval(r: dict) -> float:
            try:
                return float(r.get("p_value", 1))
            except (TypeError, ValueError):
                return 1.0

        ship = [r for r in rows if r.get("rollout_recommendation") == "ship_or_expand"]
        rollback = [r for r in rows if r.get("rollout_recommendation") == "rollback_or_redesign"]
        cont = [r for r in rows if r.get("rollout_recommendation") == "continue_test_or_segment"]
        sig = [r for r in rows if _pval(r) < 0.05]

        ship_table = "\n".join(
            f"| {r.get('experiment_id','')} | {r.get('feature_area','')} | {r.get('primary_metric','')} | +{float(r.get('lift_pct',0)):.1f}% |"
            for r in ship[:5]
        )
        md = f"""## 🔬 Experiment Analysis

**Summary:** {len(rows)} experiments | {len(sig)} statistically significant

| Decision | Count |
|----------|-------|
| 🟢 Ship or Expand | {len(ship)} |
| 🟡 Continue / Segment | {len(cont)} |
| 🔴 Rollback / Redesign | {len(rollback)} |

**Top experiments to ship:**

| Experiment | Feature Area | Metric | Lift |
|------------|--------------|--------|------|
{ship_table if ship_table else "| — | — | — | — |"}

"""
        chart = {
            "type": "bar",
            "title": "Experiment Decisions",
            "data": [
                {"name": "Ship", "value": len(ship)},
                {"name": "Continue", "value": len(cont)},
                {"name": "Rollback", "value": len(rollback)},
            ],
        }
        return md, [chart]

    def _section_anomalies(self) -> tuple[str, list]:
        rows = self._anomalies()
        if not rows:
            return "", []
        anom = [r for r in rows if str(r.get("is_anomaly", "")).lower() in ("true", "1")]
        recent = sorted(anom, key=lambda r: r.get("order_day", ""), reverse=True)[:5]
        table = "\n".join(
            f"| {r['order_day']} | ${float(r.get('revenue',0)):,.0f} | {float(r.get('cancellation_rate',0)):.1%} |"
            for r in recent
        )
        md = f"""## 🚨 Anomaly Detection

**{len(anom)} anomalous days** detected out of {len(rows)} total days.

**Most recent anomalies:**

| Date | Revenue | Cancellation Rate |
|------|---------|------------------|
{table if table else "| — | — | — |"}

"""
        chart = {
            "type": "line",
            "title": "Daily Revenue with Anomalies",
            "data": [{"name": r["order_day"], "value": float(r.get("revenue", 0)), "anomaly": str(r.get("is_anomaly","")).lower() in ("true","1")} for r in rows[-30:]],
        }
        return md, [chart]

    def _section_forecast(self) -> tuple[str, list]:
        rows = self._forecast()
        if not rows:
            return "", []
        total = sum(float(r["forecast_revenue"]) for r in rows)
        avg = total / len(rows) if rows else 0
        md = f"""## 📈 Revenue Forecast

**{len(rows)}-day forecast** using trailing mean + trend model.

- **Total projected revenue:** ${total:,.0f}
- **Avg daily revenue:** ${avg:,.0f}
- **Method:** {rows[0].get('method', 'statistical')}

| Day | Forecast Revenue |
|-----|-----------------|
{chr(10).join(f"| {r['forecast_day']} | ${float(r['forecast_revenue']):,.0f} |" for r in rows)}

"""
        chart = {
            "type": "line",
            "title": "Revenue Forecast",
            "data": [{"name": r["forecast_day"], "value": float(r["forecast_revenue"])} for r in rows],
        }
        return md, [chart]

    def _section_segments(self) -> tuple[str, list]:
        rows = self._segments()
        if not rows:
            return "", []
        table = "\n".join(
            f"| Segment {r['segment']} | {int(float(r.get('users',0))):,} | ${float(r.get('avg_spend',0)):,.0f} | {float(r.get('avg_orders',0)):.1f} |"
            for r in rows
        )
        best = max(rows, key=lambda r: float(r.get("avg_spend", 0)))
        md = f"""## 👥 User Segments

**{len(rows)} segments** identified via KMeans clustering.

| Segment | Users | Avg Spend | Avg Orders |
|---------|-------|-----------|------------|
{table}

> 💡 **Highest value segment:** Segment {best['segment']} with avg spend of ${float(best.get('avg_spend',0)):,.0f}

"""
        chart = {
            "type": "bar",
            "title": "Avg Spend by Segment",
            "data": [{"name": f"Segment {r['segment']}", "value": float(r.get("avg_spend", 0))} for r in rows],
        }
        return md, [chart]

    def _section_root_cause(self) -> tuple[str, list]:
        rows = self._root_cause()
        if not rows:
            return "", []
        items = "\n\n".join(
            f"**#{r['rank']} — {r['hypothesis']}** *(confidence: {r['confidence']})*\n- Evidence: {r['evidence']}\n- Action: {r['recommended_action']}"
            for r in rows
        )
        md = f"""## 🔍 Root Cause Hypotheses

{items}

"""
        return md, []

    def _section_decision(self) -> tuple[str, list]:
        run = self._decision_run()
        if not run:
            return "", []
        rec = run.get("recommendation", {})
        action = str(rec.get("action", "—")).upper()
        rationale = rec.get("rationale", "—")
        confidence = rec.get("confidence", "—")
        risks = rec.get("risks", [])
        next_actions = rec.get("next_actions", [])
        risk_list = "\n".join(f"- ⚠️ {r}" for r in risks)
        action_list = "\n".join(f"- ✅ {a}" for a in next_actions)
        md = f"""## 🧠 AI Decision Recommendation

**Decision: `{action}`** | Confidence: {confidence}

> {rationale}

**Risks:**
{risk_list}

**Next Actions:**
{action_list}

"""
        return md, []

    def _section_release(self) -> tuple[str, list]:
        rows = self._release()
        if not rows:
            return "", []
        risky = [r for r in rows if r.get("risk_note") == "investigate"]
        table = "\n".join(
            f"| {r.get('release_id','')} | {r.get('feature_area','')} | {r.get('release_type','')} | {r.get('nearby_anomalies',0)} | 🔴 Investigate |"
            for r in risky[:5]
        )
        md = f"""## 🚀 Release Impact

**{len(risky)} risky releases** out of {len(rows)} total.

| Release | Feature Area | Type | Nearby Anomalies | Risk |
|---------|-------------|------|-----------------|------|
{table if table else "| — | — | — | — | — |"}

"""
        return md, []

    # ── main answer builder ───────────────────────────────────────────────────
    def answer(self, question: str) -> dict:
        intents = self._intent(question)
        sections: list[str] = []
        charts: list[dict] = []

        thinking = [
            f"Detected intents: {', '.join(intents)}",
            "Loading relevant artifact data...",
        ]

        handlers = {
            "kpis": self._section_kpis,
            "revenue": self._section_revenue,
            "funnel": self._section_funnel,
            "reviews": self._section_reviews,
            "experiments": self._section_experiments,
            "anomalies": self._section_anomalies,
            "forecast": self._section_forecast,
            "segments": self._section_segments,
            "root_cause": self._section_root_cause,
            "decision": self._section_decision,
            "release": self._section_release,
        }

        for intent in intents:
            if intent in handlers:
                thinking.append(f"Analysing {intent} data...")
                md, ch = handlers[intent]()
                if md:
                    sections.append(md)
                    charts.extend(ch)

        if not sections:
            md, ch = self._section_kpis()
            sections.append(md)
            charts.extend(ch)

        thinking.append("Composing evidence-grounded response...")

        full_md = f"# Analysis: {question}\n\n" + "\n---\n".join(sections)

        return {
            "answer": full_md,
            "charts": charts,
            "thinking": thinking,
            "intents": intents,
        }
