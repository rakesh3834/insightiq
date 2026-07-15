from __future__ import annotations

import pandas as pd

from insightiq.core.contracts import DecisionQuestion
from insightiq.core.orchestrator import DecisionOrchestrator
from insightiq.knowledge.evidence_store import EvidenceStore


def test_decision_orchestrator_returns_actionable_recommendation() -> None:
    store = EvidenceStore.from_frames(
        {
            "reviews": pd.DataFrame(
                [
                    {
                        "review_id": "R1",
                        "product_id": "P1",
                        "rating": 2,
                        "review_text": "Checkout was slow and refund was delayed.",
                        "review_date": "2025-01-01",
                    }
                ]
            ),
            "products": pd.DataFrame([{"product_id": "P1", "category": "Checkout", "brand": "Acme"}]),
            "release_notes": pd.DataFrame(
                [
                    {
                        "release_id": "REL-1",
                        "release_date": "2025-01-01",
                        "feature_area": "Checkout",
                        "release_type": "feature",
                        "title": "Checkout refresh",
                        "description": "Changed checkout flow",
                        "expected_metric": "purchase_conversion",
                    }
                ]
            ),
            "engineering_incidents": pd.DataFrame(
                [
                    {
                        "incident_id": "INC-1",
                        "incident_date": "2025-01-02",
                        "severity": "SEV2",
                        "affected_area": "Checkout",
                        "customer_impact": "Checkout latency increased.",
                        "resolution": "Rolled back timeout setting.",
                    }
                ]
            ),
            "experiments": pd.DataFrame(
                [
                    {
                        "experiment_id": "EXP-1",
                        "feature_area": "Checkout",
                        "primary_metric": "purchase_conversion",
                        "lift_pct": -2.1,
                        "p_value": 0.03,
                        "decision": "rollback",
                    }
                ]
            ),
        }
    )
    artifacts = {
        "funnel": pd.DataFrame([{"step": "purchase", "users": 10}]),
        "review_intelligence": pd.DataFrame(
            [
                {
                    "category": "Checkout",
                    "brand": "Acme",
                    "topic": "slow refund",
                    "sentiment": "negative",
                    "reviews": 10,
                    "avg_sentiment": -0.2,
                    "example_review": "Checkout was slow.",
                }
            ]
        ),
        "release_impact": pd.DataFrame(
            [
                {
                    "release_id": "REL-1",
                    "feature_area": "Checkout",
                    "nearby_anomalies": 1,
                    "related_incidents": 1,
                    "risk_note": "investigate",
                }
            ]
        ),
        "experiment_decisions": pd.DataFrame(
            [
                {
                    "experiment_id": "EXP-1",
                    "feature_area": "Checkout",
                    "primary_metric": "purchase_conversion",
                    "lift_pct": -2.1,
                    "p_value": 0.03,
                    "rollout_recommendation": "rollback_or_redesign",
                }
            ]
        ),
    }
    kpis = {"purchase_conversion": 0.12, "cart_rate": 0.5, "cancellation_rate": 0.25, "completed_revenue": 1000, "avg_review_rating": 3.2}
    recommendation = DecisionOrchestrator(store).run(
        DecisionQuestion(question="Should we expand checkout rollout?", metric="purchase_conversion", feature_area="Checkout"),
        kpis,
        artifacts,
    )
    assert recommendation.action in {"investigate", "iterate", "rollback"}
    assert recommendation.findings
    assert recommendation.next_actions

