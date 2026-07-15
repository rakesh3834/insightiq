"""LangGraph workflow for InsightIQ decision intelligence."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, TypedDict

import pandas as pd

from insightiq.agents.decision_agents import CustomerVoiceAgent, ExperimentAgent, MetricsAgent, ReleaseIncidentAgent
from insightiq.core.contracts import AgentFinding, DecisionQuestion, DecisionRecommendation
from insightiq.core.orchestrator import DecisionOrchestrator
from insightiq.evaluation.decision_eval import evaluate_recommendation
from insightiq.llm.huggingface_client import HuggingFaceLLMClient, LLMResponse


class DecisionGraphState(TypedDict, total=False):
    question: DecisionQuestion
    kpis: dict[str, Any]
    artifacts: dict[str, pd.DataFrame]
    findings: list[AgentFinding]
    recommendation: DecisionRecommendation
    llm_response: LLMResponse
    used_langgraph: bool


class DecisionGraphRunner:
    """Runs the decision intelligence workflow through LangGraph when installed."""

    def __init__(self, evidence_store: Any, llm_client: HuggingFaceLLMClient | None = None) -> None:
        self.evidence_store = evidence_store
        self.llm_client = llm_client or HuggingFaceLLMClient()
        self.metrics_agent = MetricsAgent()
        self.experiment_agent = ExperimentAgent()
        self.customer_voice_agent = CustomerVoiceAgent()
        self.release_incident_agent = ReleaseIncidentAgent()

    def run(
        self,
        question: DecisionQuestion,
        kpis: dict[str, Any],
        artifacts: dict[str, pd.DataFrame],
    ) -> dict[str, Any]:
        initial: DecisionGraphState = {
            "question": question,
            "kpis": kpis,
            "artifacts": artifacts,
            "findings": [],
            "used_langgraph": False,
        }
        try:
            graph = self._build_langgraph()
            result = graph.invoke(initial)
            result["used_langgraph"] = True
        except Exception:
            result = self._run_native(initial)
            result["used_langgraph"] = False
        return self._serialize(result)

    def _build_langgraph(self) -> Any:
        from langgraph.graph import END, StateGraph

        workflow = StateGraph(DecisionGraphState)
        workflow.add_node("metrics", self._metrics_node)
        workflow.add_node("experiment", self._experiment_node)
        workflow.add_node("customer_voice", self._customer_voice_node)
        workflow.add_node("release_incident", self._release_incident_node)
        workflow.add_node("recommend", self._recommendation_node)
        workflow.add_node("llm_memo", self._llm_node)
        workflow.set_entry_point("metrics")
        workflow.add_edge("metrics", "experiment")
        workflow.add_edge("experiment", "customer_voice")
        workflow.add_edge("customer_voice", "release_incident")
        workflow.add_edge("release_incident", "recommend")
        workflow.add_edge("recommend", "llm_memo")
        workflow.add_edge("llm_memo", END)
        return workflow.compile()

    def _run_native(self, state: DecisionGraphState) -> DecisionGraphState:
        for node in [
            self._metrics_node,
            self._experiment_node,
            self._customer_voice_node,
            self._release_incident_node,
            self._recommendation_node,
            self._llm_node,
        ]:
            state.update(node(state))
        return state

    def _metrics_node(self, state: DecisionGraphState) -> DecisionGraphState:
        finding = self.metrics_agent.run(state["question"], state["kpis"], state["artifacts"])
        return {"findings": [*state.get("findings", []), finding]}

    def _experiment_node(self, state: DecisionGraphState) -> DecisionGraphState:
        finding = self.experiment_agent.run(state["question"], state["artifacts"])
        return {"findings": [*state.get("findings", []), finding]}

    def _customer_voice_node(self, state: DecisionGraphState) -> DecisionGraphState:
        finding = self.customer_voice_agent.run(state["question"], state["artifacts"], self.evidence_store)
        return {"findings": [*state.get("findings", []), finding]}

    def _release_incident_node(self, state: DecisionGraphState) -> DecisionGraphState:
        finding = self.release_incident_agent.run(state["question"], state["artifacts"], self.evidence_store)
        return {"findings": [*state.get("findings", []), finding]}

    def _recommendation_node(self, state: DecisionGraphState) -> DecisionGraphState:
        orchestrator = DecisionOrchestrator(self.evidence_store)
        recommendation = orchestrator._recommend(state["question"], state["kpis"], state.get("findings", []))
        return {"recommendation": recommendation}

    def _llm_node(self, state: DecisionGraphState) -> DecisionGraphState:
        payload = {
            "question": asdict(state["question"]),
            "recommendation": asdict(state["recommendation"]),
        }
        response = self.llm_client.summarize_decision(payload)
        return {"llm_response": response}

    def _serialize(self, state: DecisionGraphState) -> dict[str, Any]:
        recommendation = state["recommendation"]
        llm_response = state["llm_response"]
        return {
            "question": asdict(state["question"]),
            "recommendation": asdict(recommendation),
            "evaluation": evaluate_recommendation(recommendation),
            "llm": asdict(llm_response),
            "used_langgraph": bool(state.get("used_langgraph", False)),
        }
