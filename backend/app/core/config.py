"""Application configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "InsightIQ"
    version: str = "0.1.0"
    root_dir: Path = Path(__file__).resolve().parents[3]
    artifacts_dir: Path = root_dir / "artifacts"
    sqlite_path: Path = artifacts_dir / "insightiq.sqlite"


settings = Settings()

