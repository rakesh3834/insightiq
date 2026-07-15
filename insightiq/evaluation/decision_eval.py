"""Evaluation for decision intelligence outputs."""

from __future__ import annotations

from insightiq.core.contracts import DecisionRecommendation


def evaluate_recommendation(recommendation: DecisionRecommendation) -> dict[str, float | int]:
    findings = recommendation.findings
    evidence_items = [item for finding in findings for item in finding.evidence]
    evidence_coverage = sum(1 for finding in findings if finding.evidence) / max(len(findings), 1)
    avg_evidence_confidence = sum(item.confidence for item in evidence_items) / max(len(evidence_items), 1)
    risk_coverage = 1.0 if recommendation.risks else 0.0
    actionability = 1.0 if recommendation.next_actions else 0.0
    return {
        "agent_count": len(findings),
        "evidence_item_count": len(evidence_items),
        "evidence_coverage": round(evidence_coverage, 4),
        "avg_evidence_confidence": round(avg_evidence_confidence, 4),
        "risk_coverage": risk_coverage,
        "actionability": actionability,
        "recommendation_confidence": recommendation.confidence,
    }

