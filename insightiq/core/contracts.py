"""Typed contracts for decision intelligence workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


DecisionAction = Literal["launch", "iterate", "rollback", "investigate"]


@dataclass(frozen=True)
class DecisionQuestion:
    question: str
    metric: str = "purchase_conversion"
    feature_area: str | None = None
    category: str | None = None
    start_date: str | None = None
    end_date: str | None = None


@dataclass(frozen=True)
class EvidenceItem:
    source: str
    title: str
    summary: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentFinding:
    agent: str
    finding: str
    evidence: list[EvidenceItem]
    confidence: float


@dataclass(frozen=True)
class DecisionRecommendation:
    action: DecisionAction
    rationale: str
    confidence: float
    findings: list[AgentFinding]
    next_actions: list[str]
    risks: list[str]

