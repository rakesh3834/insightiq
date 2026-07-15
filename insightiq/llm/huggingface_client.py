"""Hugging Face open-source LLM client."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any


DEFAULT_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

KNOWN_METRICS = {
    "conversion": "purchase_conversion",
    "convert": "purchase_conversion",
    "funnel": "purchase_conversion",
    "checkout": "purchase_conversion",
    "cancel": "cancellation_rate",
    "refund": "cancellation_rate",
    "revenue": "completed_revenue",
    "sales": "completed_revenue",
    "gmv": "completed_revenue",
    "aov": "average_order_value",
    "order value": "average_order_value",
    "rating": "avg_review_rating",
    "review": "avg_review_rating",
    "retention": "purchase_conversion",
}


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    provider: str
    used_remote_llm: bool


class HuggingFaceLLMClient:
    """Thin wrapper around huggingface_hub.InferenceClient.

    Deployment requires HF_TOKEN or HUGGINGFACEHUB_API_TOKEN. Local tests can
    run without a token by using the deterministic fallback, but production
    calls go through Hugging Face-hosted open-source models.
    """

    def __init__(
        self,
        model: str | None = None,
        token: str | None = None,
        timeout: int = 60,
        allow_fallback: bool = True,
    ) -> None:
        self.model = model or os.getenv("HF_LLM_MODEL", DEFAULT_MODEL)
        self.token = token or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
        self.timeout = timeout
        self.allow_fallback = allow_fallback

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 700, temperature: float = 0.2) -> LLMResponse:
        if not self.token:
            if not self.allow_fallback:
                raise RuntimeError("HF_TOKEN or HUGGINGFACEHUB_API_TOKEN is required for Hugging Face LLM calls.")
            return self._fallback("missing_hf_token")

        try:
            from huggingface_hub import InferenceClient

            client = InferenceClient(token=self.token, timeout=self.timeout)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return LLMResponse(
                text=response.choices[0].message.content.strip(),
                model=self.model,
                provider="huggingface",
                used_remote_llm=True,
            )
        except Exception as exc:
            if not self.allow_fallback:
                raise
            return self._fallback(f"huggingface_error:{type(exc).__name__}")

    def summarize_decision(self, payload: dict[str, Any]) -> LLMResponse:
        system_prompt = (
            "You are InsightIQ, an AI product decision intelligence system. "
            "Write concise, evidence-grounded recommendations. Do not invent facts. "
            "Cite the provided agent findings and evidence only."
        )
        user_prompt = (
            "Create an executive decision memo from this JSON-like payload. "
            "Include decision, rationale, risks, next actions, and evidence citations.\n\n"
            f"{payload}"
        )
        return self.complete(system_prompt, user_prompt)

    def extract_intent(self, question: str, feature_areas: list[str] | None = None) -> dict[str, Any]:
        """Map a free-text question to a structured DecisionQuestion scope.

        Uses the LLM to pick the target metric / feature_area / category, and falls
        back to keyword heuristics when the LLM is unavailable or returns junk."""
        heuristic = self._heuristic_intent(question, feature_areas)
        if not self.token:
            return heuristic
        areas = ", ".join(feature_areas) if feature_areas else "Checkout, Search, Catalog, Pricing, Payments, Recommendations"
        system_prompt = (
            "You extract structured intent from a product analytics question. "
            "Respond with ONLY a compact JSON object, no prose."
        )
        user_prompt = (
            "Question: " + question + "\n\n"
            "Return JSON with keys: metric (one of purchase_conversion, cancellation_rate, "
            "completed_revenue, average_order_value, avg_review_rating), feature_area (one of: "
            f"{areas}; or null), category (a product category string or null).\n"
            'Example: {"metric": "purchase_conversion", "feature_area": "Checkout", "category": null}'
        )
        try:
            raw = self.complete(system_prompt, user_prompt, max_tokens=120, temperature=0.0)
            if not raw.used_remote_llm:
                return heuristic
            match = re.search(r"\{.*\}", raw.text, re.DOTALL)
            parsed = json.loads(match.group(0)) if match else {}
            metric = parsed.get("metric") or heuristic["metric"]
            feature_area = parsed.get("feature_area") or heuristic["feature_area"]
            category = parsed.get("category") or heuristic["category"]
            if isinstance(feature_area, str) and feature_area.lower() in {"null", "none", ""}:
                feature_area = None
            if isinstance(category, str) and category.lower() in {"null", "none", ""}:
                category = None
            return {"metric": metric, "feature_area": feature_area, "category": category}
        except Exception:
            return heuristic

    def _heuristic_intent(self, question: str, feature_areas: list[str] | None) -> dict[str, Any]:
        q = question.lower()
        metric = "purchase_conversion"
        for key, value in KNOWN_METRICS.items():
            if key in q:
                metric = value
                break
        feature_area = None
        for area in feature_areas or ["Checkout", "Search", "Catalog", "Pricing", "Payments", "Recommendations"]:
            if area.lower() in q:
                feature_area = area
                break
        return {"metric": metric, "feature_area": feature_area, "category": None}

    def synthesize_answer(
        self,
        question: str,
        recommendation: dict[str, Any],
        findings: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
    ) -> LLMResponse:
        """Write a grounded, cited answer to the user's actual question from the
        agent findings, decision, and retrieved evidence."""
        system_prompt = (
            "You are InsightIQ, an AI product decision intelligence analyst. Answer the "
            "user's question directly using ONLY the supplied agent findings and evidence. "
            "Do not invent numbers. Cite evidence as [source]. Be concise and structured: "
            "lead with the decision, then the reasoning, then risks and next steps."
        )
        finding_lines = "\n".join(
            f"- {f.get('agent')}: {f.get('finding')} (confidence {f.get('confidence')})" for f in findings
        )
        evidence_lines = "\n".join(
            f"- [{e.get('source')}] {e.get('title')}: {str(e.get('summary', ''))[:240]}" for e in evidence[:8]
        )
        user_prompt = (
            f"User question: {question}\n\n"
            f"Decision: {recommendation.get('action', 'unknown').upper()} "
            f"(confidence {recommendation.get('confidence')})\n"
            f"Rationale: {recommendation.get('rationale', '')}\n\n"
            f"Agent findings:\n{finding_lines}\n\n"
            f"Retrieved evidence:\n{evidence_lines}\n\n"
            "Write the answer now."
        )
        return self.complete(system_prompt, user_prompt, max_tokens=650, temperature=0.3)

    def _fallback(self, reason: str) -> LLMResponse:
        return LLMResponse(
            text=(
                "LLM fallback memo: remote Hugging Face generation was not executed "
                f"({reason}). The deterministic decision workflow should be used as the source of truth. "
                "Configure HF_TOKEN and HF_LLM_MODEL to enable open-source LLM generation."
            ),
            model=self.model,
            provider="huggingface",
            used_remote_llm=False,
        )

