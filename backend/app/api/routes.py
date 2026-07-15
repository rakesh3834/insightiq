"""API route declarations."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.artifact_service import ArtifactService
from ..services.chat_service import ChatService
from ..services.decision_service import DecisionService


router = APIRouter()
service = ArtifactService()
chat_service = ChatService(service)
decision_service = DecisionService(service)


class ChatRequest(BaseModel):
    question: str


@router.post("/chat")
async def chat(req: ChatRequest) -> dict:
    return chat_service.answer(req.question)


@router.post("/ask")
async def ask(req: ChatRequest) -> dict:
    """Agentic endpoint: runs the live agent workflow on the user's question."""
    return decision_service.ask(req.question)


@router.post("/reports/generate")
async def generate_report(req: ChatRequest) -> dict:
    """Regenerate a Decision Memo + Presentation tailored to the user's question."""
    return decision_service.generate_report(req.question)

@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "insightiq"}


@router.get("/metrics/summary")
async def metrics_summary() -> dict:
    return service.read_json("kpi_summary.json")


@router.get("/metrics/funnel")
async def funnel() -> list[dict]:
    return service.read_csv("funnel_summary.csv")


@router.get("/reviews/intelligence")
async def review_intelligence(limit: int = 100) -> list[dict]:
    return service.read_csv("review_intelligence.csv", limit=limit)


@router.get("/experiments/decisions")
async def experiment_decisions() -> list[dict]:
    return service.read_csv("experiment_decisions.csv")


@router.get("/root-cause/hypotheses")
async def root_cause_hypotheses() -> list[dict]:
    return service.read_csv("root_cause_hypotheses.csv")


@router.get("/decision-intelligence/run")
async def decision_intelligence_run() -> dict:
    return service.read_json("decision_intelligence_run.json")


class OrderFeatures(BaseModel):
    order_value: float = 0
    n_items: float = 1
    total_qty: float = 1
    avg_item_price: float = 0
    n_events: float = 0
    account_age_days: float = 0
    order_hour: float = 12
    is_weekend: float = 0
    gender: str = "unknown"


@router.get("/model/evaluation")
async def model_evaluation() -> dict:
    """Cancellation-risk model leaderboard, metrics, ROC curve, and feature importance."""
    return service.read_json("model_evaluation.json")


@router.get("/model/feature-selection")
async def model_feature_selection() -> dict:
    """Feature-selection comparison — MI, L1, RFECV, forward SFS, backward SBS + consensus."""
    return service.read_json("feature_selection.json")


@router.post("/model/predict")
async def model_predict(features: OrderFeatures) -> dict:
    """Score an order's cancellation risk using the persisted trained model."""
    from insightiq.ml.cancellation_model import predict as predict_cancellation

    return predict_cancellation(features.model_dump())


@router.get("/decision-intelligence/vector-db")
async def vector_db_status() -> dict:
    return service.read_json("vector_db_status.json")


@router.get("/cost/optimization")
async def cost_optimization() -> dict:
    return service.read_json("cost_optimization_report.json")


@router.get("/prd/compliance")
async def prd_compliance() -> list[dict]:
    return service.read_csv("prd_compliance_matrix.csv")


@router.get("/artifacts")
async def artifacts() -> list[str]:
    return service.list_artifacts()


@router.get("/anomalies")
async def anomalies() -> list[dict]:
    return service.read_csv("anomalies.csv")


@router.get("/forecast")
async def forecast() -> list[dict]:
    return service.read_csv("forecast.csv")


@router.get("/segments/profiles")
async def segment_profiles() -> list[dict]:
    return service.read_csv("segment_profiles.csv")


@router.get("/release/impact")
async def release_impact() -> list[dict]:
    return service.read_csv("release_impact.csv")


@router.get("/metrics/tableau")
async def tableau_extract() -> list[dict]:
    return service.read_csv("tableau_dashboard_extract.csv")


@router.get("/metrics/monthly-revenue")
async def monthly_revenue() -> list[dict]:
    return service.read_csv("monthly_revenue.csv")


@router.get("/evaluation")
async def evaluation() -> dict:
    return service.read_json("evaluation_report.json")


@router.get("/recommendations/decision")
async def decision() -> dict[str, str]:
    return {"memo": service.read_text("decision_memo.md")}


@router.get("/reports/presentation")
async def presentation() -> dict[str, str]:
    return {"presentation": service.read_text("presentation.md")}
