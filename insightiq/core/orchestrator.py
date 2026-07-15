"""Decision intelligence orchestration."""

from __future__ import annotations

from typing import Any

import pandas as pd

from insightiq.agents.decision_agents import CustomerVoiceAgent, ExperimentAgent, MetricsAgent, ReleaseIncidentAgent
from insightiq.core.contracts import AgentFinding, DecisionQuestion, DecisionRecommendation
from insightiq.knowledge.evidence_store import EvidenceStore


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

        if kpis.get("cancellation_rate", 0) > 0.18:
            risk_score += 0.25
            risks.append("Cancellation rate is above the configured decision guardrail.")
        if kpis.get("avg_review_rating", 5) < 3.5:
            risk_score += 0.15
            risks.append("Review quality is close to the risk threshold.")
        for finding in findings:
            text = finding.finding.lower()
            if any(term in text for term in ["risk", "negative", "rollback", "investigation", "investigate", "high enough"]):
                risk_score += 0.18 * finding.confidence
            if any(term in text for term in ["upside", "controlled rollout", "ship", "positive"]):
                opportunity_score += 0.2 * finding.confidence

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
        )
