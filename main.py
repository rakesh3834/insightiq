"""Start InsightIQ: FastAPI backend + Next.js frontend together."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _artifacts_ready() -> bool:
    required = ["decision_intelligence_run.json", "kpi_summary.json", "funnel_summary.csv"]
    return all((ROOT / "artifacts" / f).exists() for f in required)


def _wait_for_api(timeout: int = 30) -> bool:
    for _ in range(timeout):
        try:
            if requests.get("http://localhost:8000/health", timeout=2).ok:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def main() -> None:
    if not _artifacts_ready():
        print("⚙️  First run — generating artifacts...")
        from scripts.generate_synthetic_datasets import main as gen_synthetic
        from insightiq.pipeline import run_pipeline
        gen_synthetic()
        run_pipeline()
        print("✅ Artifacts ready.")

    # Kill stale processes
    subprocess.run(["pkill", "-f", "uvicorn backend.app.main"], capture_output=True)
    subprocess.run(["pkill", "-f", "next dev"], capture_output=True)
    time.sleep(1)

    print("🚀 Starting FastAPI on http://localhost:8000 ...")
    api_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(ROOT),
    )

    if not _wait_for_api():
        print("❌ API did not start in time.")
        api_proc.terminate()
        sys.exit(1)

    print("🌐 Starting Next.js frontend on http://localhost:3000 ...")
    ui_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(FRONTEND),
    )

    print("\n✅ InsightIQ is running:")
    print("   Frontend → http://localhost:3000")
    print("   API      → http://localhost:8000")
    print("   API Docs → http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop.\n")

    try:
        api_proc.wait()
        ui_proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        api_proc.terminate()
        ui_proc.terminate()


if __name__ == "__main__":
    main()
