"""Read pipeline artifacts for API routes."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from ..core.config import settings


class ArtifactService:
    def __init__(self, artifacts_dir: Path | None = None) -> None:
        self.artifacts_dir = artifacts_dir or settings.artifacts_dir

    def _path(self, name: str) -> Path:
        path = self.artifacts_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Artifact not found: {path}")
        return path

    def read_json(self, name: str) -> dict:
        return json.loads(self._path(name).read_text(encoding="utf-8"))

    def read_text(self, name: str) -> str:
        return self._path(name).read_text(encoding="utf-8")

    def read_csv(self, name: str, limit: int | None = None) -> list[dict]:
        with self._path(name).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        return rows[:limit] if limit else rows

    def list_artifacts(self) -> list[str]:
        if not self.artifacts_dir.exists():
            return []
        return sorted(path.name for path in self.artifacts_dir.iterdir() if path.is_file())
