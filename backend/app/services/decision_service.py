"""Agentic decision service — runs the full agent workflow on a live user question.

Unlike the batch pipeline (which answers one hardcoded question at build time),
this service takes the user's question at request time, extracts its intent,
retrieves semantically-relevant evidence, runs the four decision agents scoped to
the question, produces a recommendation, and has the LLM synthesize a grounded,
cited answer. This is the interactive `user input -> agents -> decision -> output`
flow surfaced through POST /ask.
"""

from __future__ import annotations

import functools
from typing import Any

import pandas as pd

from insightiq.core.contracts import DecisionQuestion
from insightiq.graph.decision_graph import DecisionGraphRunner
from insightiq.knowledge.chroma_store import ChromaEvidenceStore
from insightiq.llm.huggingface_client import HuggingFaceLLMClient

from ..core.config import settings
from .artifact_service import ArtifactService
from .chat_service import ChatService

AGENT_LABEL = {
    "metrics_agent": "Metrics",
    "experiment_agent": "Experiments",
    "customer_voice_agent": "Customer Voice",
    "release_incident_agent": "Release & Incidents",
}


class DecisionService:
    """Runs the live agentic decision workflow over the generated artifacts."""

    _ARTIFACT_FRAMES = {
        "funnel": "funnel_summary.csv",
        "review_intelligence": "review_intelligence.csv",
        "release_impact": "release_impact.csv",
        "experiment_decisions": "experiment_decisions.csv",
    }

    def __init__(self, artifact_service: ArtifactService | None = None) -> None:
        self.svc = artifact_service or ArtifactService()
        self.chat = ChatService(self.svc)
        self.llm = HuggingFaceLLMClient()

    # ── lazily-cached, read-only resources (loaded once per process) ──────────
    @functools.cached_property
    def _store(self) -> ChromaEvidenceStore:
        # Opens the already-indexed persistent collection; queries embed via HF.
        return ChromaEvidenceStore(settings.artifacts_dir / "chroma")

    @functools.cached_property
    def _kpis(self) -> dict[str, Any]:
        try:
            return self.svc.read_json("kpi_summary.json")
        except Exception:
            return {}

    @functools.cached_property
    def _frames(self) -> dict[str, pd.DataFrame]:
        frames: dict[str, pd.DataFrame] = {}
        for key, filename in self._ARTIFACT_FRAMES.items():
            try:
                frames[key] = pd.read_csv(self.svc._path(filename))
            except Exception:
                frames[key] = pd.DataFrame()
        return frames

    @functools.cached_property
    def _feature_areas(self) -> list[str]:
        areas: set[str] = set()
        for key in ("experiment_decisions", "release_impact"):
            frame = self._frames.get(key)
            if frame is not None and "feature_area" in frame:
                areas.update(str(a) for a in frame["feature_area"].dropna().unique())
        return sorted(areas) or ["Checkout", "Search", "Catalog", "Pricing", "Payments"]

    # ── deterministic fallback (no LLM) ──────────────────────────────────────
    def _deterministic_answer(
        self,
        question: str,
        recommendation: dict[str, Any],
        findings: list[dict[str, Any]],
        data_sections: str,
    ) -> str:
        """Build a grounded, question-specific answer from the rule-based decision
        and agent findings when the LLM is unavailable — never the raw error memo."""
        action = str(recommendation.get("action", "review")).upper()
        confidence = recommendation.get("confidence")
        conf_pct = f" (confidence {round(float(confidence) * 100)}%)" if confidence is not None else ""
        lines = [f"## Decision: {action}{conf_pct}", ""]
        if recommendation.get("rationale"):
            lines += [recommendation["rationale"], ""]
        if findings:
            lines.append("**Agent findings**")
            for f in findings:
                lines.append(f"- **{AGENT_LABEL.get(f.get('agent', ''), f.get('agent', ''))}:** {f.get('finding', '')}")
            lines.append("")
        if recommendation.get("risks"):
            lines.append("**Risks**")
            lines += [f"- {r}" for r in recommendation["risks"]] + [""]
        if recommendation.get("next_actions"):
            lines.append("**Next actions**")
            lines += [f"- {a}" for a in recommendation["next_actions"]] + [""]
        # Append the question-specific data sections (KPIs / reviews / anomalies / …).
        body = data_sections.split("\n", 2)[-1] if data_sections.startswith("# ") else data_sections
        if body.strip():
            lines += ["---", "", body.strip()]
        return "\n".join(lines)

    # ── main entry ────────────────────────────────────────────────────────────
    def ask(self, question: str) -> dict[str, Any]:
        thinking = ["Extracting decision intent from the question..."]
        intent = self.llm.extract_intent(question, self._feature_areas)
        thinking.append(
            f"Scope → metric={intent['metric']} | feature_area={intent.get('feature_area')}"
        )

        decision_question = DecisionQuestion(
            question=question,
            metric=intent["metric"],
            feature_area=intent.get("feature_area"),
            category=intent.get("category"),
        )

        thinking.append("Retrieving semantically-relevant evidence and running agents...")
        runner = DecisionGraphRunner(self._store, self.llm)
        payload = runner.run(decision_question, self._kpis, self._frames)

        recommendation = payload.get("recommendation", {})
        findings = recommendation.get("findings", [])
        evidence = [item for f in findings for item in f.get("evidence", [])]

        # Reuse the fast intent router for charts + question-specific data sections.
        chat_result = self.chat.answer(question)

        thinking.append("Synthesizing a grounded, cited answer...")
        synthesized = self.llm.synthesize_answer(question, recommendation, findings, evidence)
        if synthesized.used_remote_llm:
            answer = synthesized.text
        else:
            # LLM unavailable (e.g. HF rate-limit / 403): degrade to a real,
            # question-specific grounded answer instead of surfacing the error memo.
            thinking.append("LLM unavailable — composing a deterministic grounded answer.")
            answer = self._deterministic_answer(question, recommendation, findings, chat_result.get("answer", ""))

        return {
            "answer": answer,
            "decision": {
                "action": recommendation.get("action"),
                "confidence": recommendation.get("confidence"),
                "rationale": recommendation.get("rationale"),
                "risks": recommendation.get("risks", []),
                "next_actions": recommendation.get("next_actions", []),
                "attribution": recommendation.get("attribution", []),
            },
            "findings": [
                {"agent": f.get("agent"), "finding": f.get("finding"), "confidence": f.get("confidence")}
                for f in findings
            ],
            "citations": [
                {"source": e.get("source"), "title": e.get("title"), "summary": str(e.get("summary", ""))[:280]}
                for e in evidence[:8]
            ],
            "charts": chat_result.get("charts", []),
            "intents": chat_result.get("intents", []),
            "thinking": thinking,
            "used_remote_llm": bool(synthesized.used_remote_llm),
            "used_langgraph": bool(payload.get("used_langgraph")),
            "scope": intent,
        }

    # ── question-specific report generation ───────────────────────────────────
    def generate_report(self, question: str) -> dict[str, Any]:
        """Regenerate a Decision Memo + executive Presentation for a user's question,
        driven by the same agentic engine as /ask (retrieval → agents → decision → LLM)."""
        result = self.ask(question)
        decision = result["decision"]
        action = str(decision.get("action", "review")).upper()
        conf = decision.get("confidence")
        conf_pct = f"{round(float(conf) * 100)}%" if conf is not None else "—"
        engine = "Hugging Face LLM" if result["used_remote_llm"] else "deterministic decision engine"
        return {
            "question": question,
            "decision": decision,
            "scope": result["scope"],
            "used_remote_llm": result["used_remote_llm"],
            "memo": self._format_memo(question, result, action, conf_pct, engine),
            "presentation": self._format_presentation(question, result, action, conf_pct),
        }

    def _kpi_lines(self) -> list[str]:
        k = self._kpis
        if not k:
            return []
        return [
            f"- Completed revenue: USD {k.get('completed_revenue', 0):,.0f}",
            f"- Purchase conversion: {k.get('purchase_conversion', 0):.1%}",
            f"- Cancellation rate: {k.get('cancellation_rate', 0):.1%}",
            f"- Average order value: USD {k.get('average_order_value', 0):,.2f}",
            f"- Average review rating: {k.get('avg_review_rating', 0)} / 5",
        ]

    def _format_memo(self, question: str, result: dict[str, Any], action: str, conf_pct: str, engine: str) -> str:
        decision = result["decision"]
        lines = [
            f"# Decision Memo: {question}",
            "",
            f"**Decision:** `{action}` &nbsp;|&nbsp; **Confidence:** {conf_pct} &nbsp;|&nbsp; _Generated by {engine}_",
            "",
            "## Recommendation",
            decision.get("rationale") or "—",
            "",
            "## Agent Findings",
        ]
        lines += [f"- **{AGENT_LABEL.get(f['agent'], f['agent'])}:** {f['finding']}" for f in result["findings"]] or ["- —"]
        if result["citations"]:
            lines += ["", "## Supporting Evidence"]
            lines += [f"- **[{c['source']}]** {c['title']} — {c['summary']}" for c in result["citations"][:6]]
        if decision.get("risks"):
            lines += ["", "## Risks"] + [f"- {r}" for r in decision["risks"]]
        if decision.get("next_actions"):
            lines += ["", "## Next Actions"] + [f"- {a}" for a in decision["next_actions"]]
        if self._kpi_lines():
            lines += ["", "## KPI Context"] + self._kpi_lines()
        return "\n".join(lines)

    def _format_presentation(self, question: str, result: dict[str, Any], action: str, conf_pct: str) -> str:
        decision = result["decision"]
        findings = "\n".join(f"- **{AGENT_LABEL.get(f['agent'], f['agent'])}:** {f['finding']}" for f in result["findings"])
        risks = "\n".join(f"- {r}" for r in decision.get("risks", [])) or "- No major risk crossed the guardrail."
        actions = "\n".join(f"- {a}" for a in decision.get("next_actions", [])) or "- —"
        return "\n".join([
            f"# {question}",
            "",
            "## Executive Summary",
            f"**Decision: {action}** ({conf_pct} confidence)",
            "",
            decision.get("rationale") or "—",
            "",
            "## The Evidence",
            findings or "- —",
            "",
            "## Metrics Snapshot",
            *self._kpi_lines(),
            "",
            "## Risks & Watch-outs",
            risks,
            "",
            "## Recommended Next Steps",
            actions,
        ])
