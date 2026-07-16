"""Decision intelligence orchestration."""

from __future__ import annotations

from typing import Any

import pandas as pd

from insightiq.agents.decision_agents import CustomerVoiceAgent, ExperimentAgent, MetricsAgent, ReleaseIncidentAgent
from insightiq.core.contracts import AgentFinding, DecisionQuestion, DecisionRecommendation
from insightiq.knowledge.evidence_store import EvidenceStore


# Human-readable names for each evidence stream, shown in the explainability card.
AGENT_LABELS = {
    "metrics_agent": "Revenue & KPIs",
    "experiment_agent": "Experiments",
    "customer_voice_agent": "Customer Reviews",
    "release_incident_agent": "Release & Incidents",
}

_RISK_TERMS = ["risk", "negative", "rollback", "investigation", "investigate", "high enough"]
_OPPORTUNITY_TERMS = ["upside", "controlled rollout", "ship", "positive"]


class DecisionOrchestrator:
    """Runs the evidence-grounded decision workflow.

    The class is intentionally simple and deterministic. The deployment workflow
    uses the same stage boundaries inside LangGraph.
    """

    def __init__(self, store: EvidenceStore) -> None:
        self.store = store
        self.metrics_agent = MetricsAgent()
        self.experiment_agent = ExperimentAgent()
        self.customer_voice_agent = CustomerVoiceAgent()
        self.release_incident_agent = ReleaseIncidentAgent()

    def run(self, question: DecisionQuestion, kpis: dict[str, Any], artifacts: dict[str, pd.DataFrame]) -> DecisionRecommendation:
        findings = [
            self.metrics_agent.run(question, kpis, artifacts),
            self.experiment_agent.run(question, artifacts),
            self.customer_voice_agent.run(question, artifacts, self.store),
            self.release_incident_agent.run(question, artifacts, self.store),
        ]
        return self._recommend(question, kpis, findings)

    def _recommend(self, question: DecisionQuestion, kpis: dict[str, Any], findings: list[AgentFinding]) -> DecisionRecommendation:
        risk_score = 0.0
        opportunity_score = 0.0
        risks: list[str] = []
        next_actions = [
            "Validate the highest-impact SQL metrics against the warehouse.",
            "Inspect release, incident, and feature-flag timelines for the affected feature area.",
            "Review negative customer themes before expanding rollout.",
        ]

        # Track how much each evidence stream contributes to the decision so the
        # confidence score can be explained (weights sum to 100 after normalizing).
        # A small baseline keeps every stream visible; directional signals add weight.
        contribution: dict[str, float] = {f.agent: 0.08 * f.confidence for f in findings}
        direction: dict[str, str] = {f.agent: "informational" for f in findings}

        if kpis.get("cancellation_rate", 0) > 0.18:
            risk_score += 0.25
            risks.append("Cancellation rate is above the configured decision guardrail.")
            if "metrics_agent" in contribution:
                contribution["metrics_agent"] += 0.25
                direction["metrics_agent"] = "risk"
        if kpis.get("avg_review_rating", 5) < 3.5:
            risk_score += 0.15
            risks.append("Review quality is close to the risk threshold.")
            if "customer_voice_agent" in contribution:
                contribution["customer_voice_agent"] += 0.15
                direction["customer_voice_agent"] = "risk"
        for finding in findings:
            text = finding.finding.lower()
            if any(term in text for term in _RISK_TERMS):
                risk_score += 0.18 * finding.confidence
                contribution[finding.agent] += 0.18 * finding.confidence
                direction[finding.agent] = "risk"
            if any(term in text for term in _OPPORTUNITY_TERMS):
                opportunity_score += 0.2 * finding.confidence
                contribution[finding.agent] += 0.2 * finding.confidence
                if direction[finding.agent] != "risk":
                    direction[finding.agent] = "opportunity"

        if risk_score >= 0.55:
            action = "investigate"
            rationale = "Multiple evidence streams show risk; the safest decision is to investigate before expanding rollout."
        elif opportunity_score > risk_score and opportunity_score >= 0.25:
            action = "iterate"
            rationale = "Experiment evidence suggests upside, but rollout should remain controlled until guardrails are stable."
        elif risk_score >= 0.35:
            action = "iterate"
            rationale = "There are moderate risks; iterate on the affected area before full launch."
        else:
            action = "launch"
            rationale = "Evidence does not cross risk thresholds, and product metrics are within launch guardrails."

        confidence = min(0.92, max(0.55, 0.58 + abs(opportunity_score - risk_score)))
        return DecisionRecommendation(
            action=action,
            rationale=rationale,
            confidence=round(confidence, 3),
            findings=findings,
            next_actions=next_actions,
            risks=risks or ["No major risk crossed the configured threshold."],
            attribution=self._attribution(findings, contribution, direction),
        )

    @staticmethod
    def _attribution(
        findings: list[AgentFinding],
        contribution: dict[str, float],
        direction: dict[str, str],
    ) -> list[dict[str, Any]]:
        """Normalize each stream's contribution into weights that sum to 100."""
        total = sum(contribution.values()) or 1.0
        conf_by_agent = {f.agent: f.confidence for f in findings}
        weights = sorted(
            (
                {
                    "agent": agent,
                    "label": AGENT_LABELS.get(agent, agent),
                    "weight": round(100 * value / total, 1),
                    "direction": direction.get(agent, "informational"),
                    "confidence": round(conf_by_agent.get(agent, 0.0), 2),
                }
                for agent, value in contribution.items()
            ),
            key=lambda d: d["weight"],
            reverse=True,
        )
        # Absorb rounding drift into the largest stream so the bars total exactly 100.
        if weights:
            drift = round(100.0 - sum(w["weight"] for w in weights), 1)
            weights[0]["weight"] = round(weights[0]["weight"] + drift, 1)
        return weights
