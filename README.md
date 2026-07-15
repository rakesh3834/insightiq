# InsightIQ

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://insightiq.streamlit.app)

InsightIQ is an AI Decision Intelligence Platform for product, data, and engineering teams. It turns ecommerce behavior, orders, reviews, release notes, experiments, incidents, and product documentation into evidence-grounded product decisions.

It is intentionally not a chatbot-first project and not a dashboard-first project. The main artifact is a decision workflow that answers business questions with metrics, customer voice, experiment evidence, release context, root-cause hypotheses, recommendations, and evaluation.

## GitHub First Run

Clone the project, create a Hugging Face token, and configure the environment:

```bash
cp .env.example .env
export HF_TOKEN=your_huggingface_token
pip install -r requirements.txt
python scripts/run_all.py
python scripts/start_api.py
```

The API will be available at `http://localhost:8000`.

Docker path:

```bash
cp .env.example .env
docker compose up --build
```

The pipeline automatically discovers the local `ecommerce_dataset/` folder. It builds a SQLite/DuckDB-compatible warehouse, indexes evidence into Chroma when installed, runs LangGraph decision orchestration, calls a Hugging Face open-source LLM when `HF_TOKEN` is configured, and writes decision artifacts.

The ecommerce CSVs are the source of truth. Public ecommerce data does not contain internal product-management context, so InsightIQ synthesizes release notes, A/B tests, feature flags, engineering incidents, business glossary entries, and product documentation from the real category, brand, and order-date distribution.

Expected outputs are written to `artifacts/`:

- `insightiq.sqlite`
- `kpi_summary.json`
- `funnel_summary.csv`
- `tableau_dashboard_extract.csv`
- `review_intelligence.csv`
- `segment_profiles.csv`
- `anomalies.csv`
- `forecast.csv`
- `decision_memo.md`
- `presentation.md`
- `evaluation_report.json`
- `experiment_decisions.csv`
- `root_cause_hypotheses.csv`
- `decision_intelligence_run.json`
- `decision_intelligence_run.md`
- `vector_db_status.json`
- `cost_optimization_report.json`
- `prd_compliance_matrix.csv`
- `generated_fastapi_app.py`

## Product Workflow

InsightIQ follows this decision loop:

1. Open Mixpanel: inspect event funnels, activation, retention, and drop-offs.
2. Open Tableau: review BI dashboards for revenue, category, cohort, and segment performance.
3. Write SQL: validate the metric movement directly from the warehouse.
4. Ask Data Scientist: run forecasting, anomaly detection, segmentation, sentiment, and topic analysis.
5. Read Reviews: connect qualitative pain points to product and revenue metrics.
6. Read Release Notes: correlate launches, feature flags, experiments, and incidents with metric movement.
7. Create Presentation: produce an executive narrative with evidence and trade-offs.
8. Decision: recommend launch, iterate, rollback, or investigate.

## Architecture

See [docs/architecture.md](/Users/rakesh/Desktop/InsighIQ/docs/architecture.md) for the full production architecture and [docs/product_requirements.md](/Users/rakesh/Desktop/InsighIQ/docs/product_requirements.md) for MVP scope, KPIs, target users, edge cases, and resume positioning.

The rebuilt Decision Intelligence architecture is documented in [docs/decision_intelligence_architecture.md](/Users/rakesh/Desktop/InsighIQ/docs/decision_intelligence_architecture.md).

## Tech Stack

- FastAPI and Uvicorn for the API.
- LangGraph `StateGraph` for agent workflow orchestration.
- Hugging Face `InferenceClient` for open-source LLM calls.
- Chroma persistent vector DB for evidence retrieval.
- SQLite plus optional DuckDB for warehouse analytics.
- Pandas, NumPy, and scikit-learn for data science.
- Streamlit for a minimal demo UI.
- Docker, Render config, and GitHub Actions for deployment readiness.

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_synthetic_datasets.py
python scripts/run_all.py
pytest
```

Use `python3` instead of `python` on machines where only `python3` is installed.

The backend lives under `backend/` and exposes the generated decision intelligence artifacts through FastAPI. The core AI workflow lives under `insightiq/`.

## Deploy

Run the complete workflow locally:

```bash
python scripts/run_all.py
```

Start the API after artifacts are generated:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Render-style deployment config is available at [deployment/render.yaml](/Users/rakesh/Desktop/InsighIQ/deployment/render.yaml). Resume and interview positioning is available at [docs/resume_project_case_study.md](/Users/rakesh/Desktop/InsighIQ/docs/resume_project_case_study.md).

Minimal demo UI:

```bash
streamlit run demo/streamlit_app.py
```
