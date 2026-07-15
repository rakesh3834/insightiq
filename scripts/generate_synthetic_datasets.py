"""Generate support datasets unavailable from public ecommerce data."""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
from random import Random

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_synthetic"
DATASET = ROOT / "ecommerce_dataset"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def dataset_context() -> tuple[list[str], list[str], date, date]:
    products_path = DATASET / "products.csv"
    orders_path = DATASET / "orders.csv"
    default_start = date(2025, 1, 15)
    default_end = date(2025, 11, 15)
    if not products_path.exists() or not orders_path.exists():
        return ["Search", "Checkout", "Recommendations", "Reviews", "Pricing", "Mobile"], ["InsightIQ"], default_start, default_end

    products = pd.read_csv(products_path, usecols=["category", "brand"])
    orders = pd.read_csv(orders_path, usecols=["order_date"])
    order_dates = pd.to_datetime(orders["order_date"], errors="coerce").dropna()
    categories = products["category"].dropna().astype(str).value_counts().head(8).index.tolist()
    brands = products["brand"].dropna().astype(str).value_counts().head(8).index.tolist()
    start = order_dates.min().date() if not order_dates.empty else default_start
    end = order_dates.max().date() if not order_dates.empty else default_end
    return categories + ["Search", "Checkout", "Recommendations", "Reviews"], brands, start, end


def main() -> None:
    rng = Random(42)
    np_rng = np.random.default_rng(42)
    feature_areas, brands, start, end = dataset_context()
    total_days = max((end - start).days, 180)
    metrics = ["purchase_conversion", "cart_rate", "refund_rate", "review_rating", "revenue"]

    releases = []
    experiments = []
    flags = []
    incidents = []
    glossary = []
    docs = []

    for i in range(24):
        release_date = start + timedelta(days=round((i + 1) * total_days / 26))
        area = feature_areas[i % len(feature_areas)]
        metric = metrics[i % len(metrics)]
        owner = brands[i % len(brands)] if brands else "Product"
        releases.append(
            {
                "release_id": f"REL-{i + 1:03d}",
                "release_date": release_date.isoformat(),
                "feature_area": area,
                "release_type": rng.choice(["feature", "experiment", "bugfix", "performance"]),
                "title": f"{area} improvement wave {i + 1}",
                "description": f"Improved {area.lower()} experience for {owner} traffic to reduce friction and improve {metric}.",
                "expected_metric": metric,
            }
        )
        # Realistic A/B experiment: sample sizes + conversion counts per arm from a
        # base rate and a true (often null) effect. Significance is computed downstream
        # via a two-proportion z-test on these actual counts — not pre-set p-values.
        base_rate = rng.uniform(0.10, 0.24)
        # ~45% of experiments have a genuine effect; the rest are null (true lift ≈ 0).
        true_lift_rel = rng.gauss(0.12, 0.06) if rng.random() < 0.45 else rng.gauss(0.0, 0.01)
        control_n = int(rng.randint(4000, 12000))
        variant_n = int(rng.randint(4000, 12000))
        variant_rate = float(min(max(base_rate * (1 + true_lift_rel), 0.001), 0.6))
        control_conv = int(np_rng.binomial(control_n, base_rate))
        variant_conv = int(np_rng.binomial(variant_n, variant_rate))
        experiments.append(
            {
                "experiment_id": f"EXP-{i + 1:03d}",
                "feature_area": area,
                "start_date": release_date.isoformat(),
                "end_date": (release_date + timedelta(days=14)).isoformat(),
                "variant": rng.choice(["A: control / B: simplified UX", "A: current / B: personalized ranking"]),
                "primary_metric": metric,
                "control_users": control_n,
                "variant_users": variant_n,
                "control_conversions": control_conv,
                "variant_conversions": variant_conv,
            }
        )
        flags.append(
            {
                "flag_id": f"FLAG-{i + 1:03d}",
                "feature_area": area,
                "flag_name": f"{area.lower()}_release_{i + 1}",
                "enabled_pct": rng.choice([10, 25, 50, 75, 100]),
                "owner": rng.choice(["product", "growth", "platform", "mobile"]),
                "status": rng.choice(["active", "graduated", "paused"]),
            }
        )

    for i in range(14):
        area = rng.choice(feature_areas)
        incidents.append(
            {
                "incident_id": f"INC-{i + 1:03d}",
                "incident_date": (start + timedelta(days=round((i + 1) * total_days / 16))).isoformat(),
                "severity": rng.choice(["SEV1", "SEV2", "SEV3"]),
                "affected_area": area,
                "duration_minutes": rng.randint(18, 240),
                "customer_impact": f"Some users experienced degraded {area.lower()} performance.",
                "resolution": "Mitigation shipped and follow-up monitoring added.",
            }
        )

    glossary.extend(
        [
            {"term": "North Star Metric", "definition": "Share of product decisions backed by complete evidence."},
            {"term": "Cart Rate", "definition": "Users who add at least one viewed product to cart."},
            {"term": "Purchase Conversion", "definition": "Users with completed orders divided by product viewers."},
            {"term": "Review Intelligence", "definition": "Qualitative review themes mapped to product metrics."},
            {"term": "Root Cause Analysis", "definition": "A ranked set of hypotheses supported by metrics, events, reviews, experiments, and release context."},
            {"term": "Decision Scientist", "definition": "A role focused on translating product data, experimentation, and business metrics into decisions."},
        ]
    )
    docs.extend(
        [
            {
                "doc_id": "DOC-001",
                "title": "Launch Review Playbook",
                "content": "Every launch decision must cite event, revenue, review, experiment, and incident evidence.",
            },
            {
                "doc_id": "DOC-002",
                "title": "Rollback Criteria",
                "content": "Rollback when revenue, conversion, or review sentiment declines with clear release correlation.",
            },
            {
                "doc_id": "DOC-003",
                "title": "InsightIQ Product PRD",
                "content": "The platform simulates a PM workflow: open Mixpanel, open Tableau, write SQL, ask a data scientist, read reviews, read release notes, create a presentation, and make a decision.",
            },
            {
                "doc_id": "DOC-004",
                "title": "Cost Optimization Playbook",
                "content": "Use prompt caching, batch processing, parallel workers, retrieval filtering, and response caching before scaling LLM workloads.",
            },
        ]
    )

    write_csv(OUT / "release_notes.csv", releases)
    write_csv(OUT / "ab_tests.csv", experiments)
    write_csv(OUT / "feature_flags.csv", flags)
    write_csv(OUT / "engineering_incidents.csv", incidents)
    write_csv(OUT / "business_glossary.csv", glossary)
    write_csv(OUT / "product_documentation.csv", docs)
    print(f"Wrote synthetic datasets to {OUT}")


if __name__ == "__main__":
    main()
