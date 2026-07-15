"""Tests for the advanced-ML upgrades: semantic embeddings, intent extraction,
transformer-backed sentiment, and interval forecasting. These force the offline
fallbacks (no HF token) so they are deterministic and network-free in CI."""

from __future__ import annotations

import numpy as np
import pandas as pd

import pytest

from insightiq.knowledge.chroma_store import HFEmbeddingFunction
from insightiq.llm.huggingface_client import HuggingFaceLLMClient
from insightiq.pipeline import ARTIFACTS, forecast_revenue


@pytest.fixture
def _preserve_forecast_artifact():
    """forecast_revenue writes artifacts/forecast.csv as a side effect; keep the
    real pipeline artifact intact when the test exercises it with toy data."""
    path = ARTIFACTS / "forecast.csv"
    backup = path.read_bytes() if path.exists() else None
    yield
    if backup is not None:
        path.write_bytes(backup)
    elif path.exists():
        path.unlink()


@pytest.fixture
def _no_hf_token(monkeypatch):
    """Remove the ambient HF token so *_(token=None) constructors take the
    deterministic offline fallback instead of the loaded .env token."""
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGINGFACEHUB_API_TOKEN", raising=False)


def test_hf_embedding_falls_back_to_hash_without_token(_no_hf_token) -> None:
    ef = HFEmbeddingFunction(token=None)  # no token → deterministic hash fallback
    vectors = ef(["checkout is broken", "checkout is broken", "fast delivery"])
    assert len(vectors) == 3
    assert all(len(v) == 384 for v in vectors)
    # identical text → identical vector (deterministic)
    assert vectors[0] == vectors[1]
    # unit-normalized
    assert abs(float(np.linalg.norm(vectors[0])) - 1.0) < 1e-5


def test_heuristic_intent_maps_keywords_to_metric(_no_hf_token) -> None:
    client = HuggingFaceLLMClient(token=None)  # no token → heuristic path
    assert client.extract_intent("why is checkout conversion dropping?")["metric"] == "purchase_conversion"
    assert client.extract_intent("are refunds increasing?")["metric"] == "cancellation_rate"
    scoped = client.extract_intent("issues in the Search experience", ["Checkout", "Search"])
    assert scoped["feature_area"] == "Search"


def test_forecast_returns_confidence_intervals(_preserve_forecast_artifact) -> None:
    days = pd.date_range("2025-01-01", periods=40, freq="D")
    orders = pd.DataFrame(
        {
            "order_status": ["completed"] * 40,
            "order_date": days,
            "total_amount": [1000 + 50 * (i % 7) for i in range(40)],
        }
    )
    forecast = forecast_revenue({"orders": orders}, horizon_days=14)
    assert len(forecast) == 14
    for column in ("forecast_day", "forecast_revenue", "lower", "upper", "method"):
        assert column in forecast.columns
    # interval brackets the point forecast
    assert (forecast["lower"] <= forecast["forecast_revenue"]).all()
    assert (forecast["upper"] >= forecast["forecast_revenue"]).all()
