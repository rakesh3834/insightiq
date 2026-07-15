"""InsightIQ decision intelligence package."""

from pathlib import Path

try:
    from dotenv import load_dotenv

    # Load the project-root .env so HF_TOKEN / HF_LLM_MODEL and other settings are
    # available to every entry point (pipeline, LangGraph LLM client, backend).
    # Real environment variables take precedence over .env values (override=False).
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:
    # python-dotenv is optional; fall back to the ambient environment if absent.
    pass
