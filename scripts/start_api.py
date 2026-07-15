"""Build artifacts if needed, then start the FastAPI app."""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from insightiq.pipeline import run_pipeline
from scripts.generate_synthetic_datasets import main as generate_synthetic


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def should_rebuild() -> bool:
    if os.getenv("INSIGHTIQ_REBUILD_ON_START", "false").lower() == "true":
        return True
    required = [
        "decision_intelligence_run.json",
        "vector_db_status.json",
        "kpi_summary.json",
        "insightiq.sqlite",
    ]
    return any(not (ARTIFACTS / name).exists() for name in required)


def main() -> None:
    if should_rebuild():
        generate_synthetic()
        run_pipeline()
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
