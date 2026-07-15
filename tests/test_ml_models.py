"""Tests for the A/B two-proportion z-test and the cancellation-risk model's
feature engineering + realistic label. Pure/deterministic — no disk side effects."""

from __future__ import annotations

import numpy as np
import pandas as pd

from insightiq.ml.cancellation_model import build_feature_frame, _realistic_cancellation_label
from insightiq.pipeline import two_proportion_ztest


def test_two_proportion_ztest_detects_real_effect() -> None:
    # 5% vs 8% on large samples → strongly significant, positive z.
    z, p = two_proportion_ztest(c_conv=500, c_n=10000, v_conv=800, v_n=10000)
    assert z > 0
    assert p < 0.01


def test_two_proportion_ztest_null_effect_not_significant() -> None:
    # Nearly identical rates → not significant.
    z, p = two_proportion_ztest(c_conv=500, c_n=10000, v_conv=505, v_n=10000)
    assert p > 0.05


def test_two_proportion_ztest_guards_zero_denominator() -> None:
    assert two_proportion_ztest(0, 0, 0, 0) == (0.0, 1.0)


def _toy_frames(n: int = 800) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(0)
    days = pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 300, n), unit="D")
    orders = pd.DataFrame({
        "order_id": [f"O{i}" for i in range(n)],
        "user_id": [f"U{i % 200}" for i in range(n)],
        "order_date": days,
        "order_status": "processing",
        "total_amount": rng.uniform(20, 2000, n),
    })
    users = pd.DataFrame({
        "user_id": [f"U{i}" for i in range(200)],
        "gender": rng.choice(["male", "female"], 200),
        "signup_date": pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 300, 200), unit="D"),
    })
    items = pd.DataFrame({
        "order_item_id": range(n), "order_id": orders["order_id"],
        "product_id": "P1", "user_id": orders["user_id"],
        "quantity": rng.integers(1, 6, n), "item_price": rng.uniform(10, 500, n), "item_total": 0,
    })
    events = pd.DataFrame({
        "event_id": range(n * 2), "user_id": [f"U{i % 200}" for i in range(n * 2)],
        "product_id": "P1", "event_type": "view", "event_timestamp": pd.Timestamp("2025-01-01"),
    })
    return {"orders": orders, "users": users, "order_items": items, "events": events}


def test_feature_frame_has_expected_features() -> None:
    df = build_feature_frame(_toy_frames())
    for col in ["order_value", "n_items", "total_qty", "avg_item_price", "n_events", "account_age_days", "order_hour", "is_weekend", "gender"]:
        assert col in df.columns
    assert df["account_age_days"].min() >= 0


def test_realistic_label_is_binary_and_reasonable_base_rate() -> None:
    df = build_feature_frame(_toy_frames())
    y = _realistic_cancellation_label(df)
    assert set(np.unique(y)).issubset({0, 1})
    assert 0.05 < y.mean() < 0.6  # a sensible cancellation base rate


def test_feature_selection_design_matrix() -> None:
    from insightiq.ml.feature_selection import _design_matrix

    df = build_feature_frame(_toy_frames())
    X, names = _design_matrix(df)
    assert X.shape[0] == len(df)
    assert "order_value" in names and "account_age_days" in names
    assert any(n.startswith("gender") for n in names)  # categorical one-hot expanded
