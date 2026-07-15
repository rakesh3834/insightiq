from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "ecommerce_dataset"


def test_required_csvs_exist() -> None:
    expected = {"users.csv", "products.csv", "orders.csv", "order_items.csv", "events.csv", "reviews.csv"}
    assert expected.issubset({path.name for path in DATASET.glob("*.csv")})


def test_primary_keys_are_unique() -> None:
    keys = {
        "users.csv": "user_id",
        "products.csv": "product_id",
        "orders.csv": "order_id",
        "order_items.csv": "order_item_id",
        "events.csv": "event_id",
        "reviews.csv": "review_id",
    }
    for filename, key in keys.items():
        frame = pd.read_csv(DATASET / filename, usecols=[key])
        assert frame[key].is_unique, f"{filename} has duplicate {key}"


def test_order_items_reference_products() -> None:
    products = set(pd.read_csv(DATASET / "products.csv", usecols=["product_id"])["product_id"])
    item_products = set(pd.read_csv(DATASET / "order_items.csv", usecols=["product_id"])["product_id"])
    assert item_products.issubset(products)

