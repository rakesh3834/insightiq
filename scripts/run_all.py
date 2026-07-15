"""Run the complete local InsightIQ workflow."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from insightiq.pipeline import _logger, run_pipeline
from scripts.generate_synthetic_datasets import main as generate_synthetic


def main() -> None:
    _logger.info("========== run_all.py START ==========")
    _logger.info("[PRE-STEP] Generating synthetic datasets (release notes, experiments, incidents, flags)")
    generate_synthetic()
    _logger.info("[PRE-STEP] Synthetic datasets ready")
    artifacts = run_pipeline()
    _logger.info(f"run_all.py DONE | decision={artifacts.decision.upper()} | artifacts={len(artifacts.output_files)} | elapsed={round(artifacts.elapsed_seconds, 2)}s")
    print(f"Decision: {artifacts.decision.upper()}")
    print(f"Artifacts: {len(artifacts.output_files)}")
    print(f"Log: {ROOT / 'logs' / 'pipeline.log'}")


if __name__ == "__main__":
    main()
