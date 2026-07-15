"""Deterministic agents for the InsightIQ decision workflow.

These are intentionally deterministic agent tools for reliable evaluation. The
workflow wraps them as LangGraph nodes and uses the Hugging Face LLM after
evidence retrieval.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from insightiq.core.contracts import AgentFinding, DecisionQuestion, EvidenceItem
from insightiq.knowledge.evidence_store import EvidenceStore


class MetricsAgent:
    name = "metrics_agent"

    def run(self, question: DecisionQuestion, kpis: dict[str, Any], artifacts: dict[str, pd.DataFrame]) -> AgentFinding:
        funnel = artifacts.get("funnel", pd.DataFrame())
        evidence = [
            EvidenceItem(
                source="kpi_summary",
                title="KPI Summary",
                summary=(
                    f"Purchase conversion {kpis.get('purchase_conversion', 0):.1%}, "
                    f"cart rate {kpis.get('cart_rate', 0):.1%}, cancellation rate {kpis.get('cancellation_rate', 0):.1%}, "
                    f"completed revenue USD {kpis.get('completed_revenue', 0):,.2f}."
                ),
                confidence=1.0,
                metadata={"metric": question.metric},
            )
        ]
        if not funnel.empty:
            evidence.append(
                EvidenceItem(
                    source="funnel_summary",
                    title="Behavior Funnel",
                    summary=funnel.to_dict(orient="records").__repr__()[:500],
                    confidence=1.0,
                    metadata={"rows": len(funnel)},
                )
            )
        finding = "Core product metrics are measurable and grounded in warehouse outputs."
        if kpis.get("cancellation_rate", 0) > 0.18:
            finding = "Cancellation rate is high enough to require investigation before broad rollout."
        return AgentFinding(agent=self.name, finding=finding, evidence=evidence, confidence=0.86)


class ExperimentAgent:
    name = "experiment_agent"

    def run(self, question: DecisionQuestion, artifacts: dict[str, pd.DataFrame]) -> AgentFinding:
        experiments = artifacts.get("experiment_decisions", pd.DataFrame())
        if experiments.empty:
            return AgentFinding(self.name, "No experiment evidence is available.", [], 0.4)
        relevant = experiments
        if question.feature_area and "feature_area" in experiments:
            filtered = experiments[experiments["feature_area"].astype(str).str.lower().eq(question.feature_area.lower())]
            if not filtered.empty:
                relevant = filtered
        top = relevant.sort_values(["p_value", "lift_pct"], ascending=[True, False]).head(3)
        evidence = [
            EvidenceItem(
                source="experiment_decisions",
                title=str(row["experiment_id"]),
                summary=f"{row['feature_area']} changed {row['primary_metric']} by {row['lift_pct']}% with p={row['p_value']}; recommendation {row['rollout_recommendation']}.",
                confidence=max(0.45, 1 - float(row["p_value"])),
                metadata=row.to_dict(),
            )
            for _, row in top.iterrows()
        ]
        positives = top[top["rollout_recommendation"].eq("ship_or_expand")]
        finding = "Experiment evidence is inconclusive; continue testing or segment the rollout."
        confidence = 0.62
        if not positives.empty:
            finding = "At least one experiment shows statistically useful upside for a controlled rollout."
            confidence = 0.82
        if (top["rollout_recommendation"] == "rollback_or_redesign").any():
            finding = "Experiment evidence contains rollback or redesign signals."
            confidence = 0.84
        return AgentFinding(self.name, finding, evidence, confidence)


class CustomerVoiceAgent:
    name = "customer_voice_agent"

    def run(self, question: DecisionQuestion, artifacts: dict[str, pd.DataFrame], store: EvidenceStore) -> AgentFinding:
        review_summary = artifacts.get("review_intelligence", pd.DataFrame())
        filters = {"category": question.category} if question.category else None
        evidence = store.search(question.question, top_k=5, filters=filters)
        if review_summary.empty:
            return AgentFinding(self.name, "No review intelligence is available.", evidence, 0.4)
        negative = review_summary[review_summary["sentiment"].eq("negative")] if "sentiment" in review_summary else pd.DataFrame()
        if negative.empty:
            finding = "Customer review evidence does not show a dominant negative theme."
            confidence = 0.65
        else:
            worst = negative.sort_values(["reviews", "avg_sentiment"], ascending=[False, True]).head(1).iloc[0]
            finding = f"Customer reviews highlight a negative theme in {worst['category']} / {worst['brand']}: {worst['topic']}."
            confidence = 0.76
        return AgentFinding(self.name, finding, evidence, confidence)


class ReleaseIncidentAgent:
    name = "release_incident_agent"

    def run(self, question: DecisionQuestion, artifacts: dict[str, pd.DataFrame], store: EvidenceStore) -> AgentFinding:
        release_impact = artifacts.get("release_impact", pd.DataFrame())
        filters = {"feature_area": question.feature_area} if question.feature_area else None
        evidence = store.search(question.question, top_k=6, filters=filters)
        if release_impact.empty:
            return AgentFinding(self.name, "No release or incident evidence is available.", evidence, 0.45)
        risky = release_impact[release_impact["risk_note"].eq("investigate")]
        if question.feature_area and "feature_area" in risky:
            scoped = risky[risky["feature_area"].astype(str).str.lower().eq(question.feature_area.lower())]
            if not scoped.empty:
                risky = scoped
        if risky.empty:
            return AgentFinding(self.name, "Release and incident context does not show a major risk signal.", evidence, 0.66)
        top = risky.sort_values(["nearby_anomalies", "related_incidents"], ascending=False).head(1).iloc[0]
        finding = f"{top['feature_area']} has release or incident risk around {top['release_id']}."
        return AgentFinding(self.name, finding, evidence, 0.79)
