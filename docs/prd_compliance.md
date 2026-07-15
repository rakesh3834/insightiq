# PRD Compliance

InsightIQ follows the attached PRD by treating the given ecommerce dataset as the primary data source and synthesizing only the internal context that public ecommerce data does not provide.

## Given Data Used

- ecommerce_dataset/users.csv
- ecommerce_dataset/products.csv
- ecommerce_dataset/events.csv
- ecommerce_dataset/orders.csv
- ecommerce_dataset/order_items.csv
- ecommerce_dataset/reviews.csv

## Synthetic Data Created

- Release notes.
- A/B tests.
- Feature flags.
- Engineering incidents.
- Business glossary.
- Product documentation.

The synthetic generator reads the real product categories, brands, and order-date range before creating support data.

## Required Workflow Mapping

- Open Mixpanel: artifacts/funnel_summary.csv.
- Open Tableau: artifacts/tableau_dashboard_extract.csv.
- Write SQL: database/analytics_queries.sql.
- Ask Data Scientist: artifacts/anomalies.csv, artifacts/forecast.csv, artifacts/segment_profiles.csv.
- Read Reviews: artifacts/review_intelligence.csv.
- Read Release Notes: artifacts/release_impact.csv.
- Create Presentation: artifacts/presentation.md.
- Decision: artifacts/decision_memo.md.

## Deployment Mapping

- Decision pipeline: insightiq/pipeline.py.
- CLI/runtime entrypoint: scripts/run_all.py and scripts/start_api.py.
- FastAPI backend: backend/app/main.py.
- LangGraph workflow: insightiq/graph/decision_graph.py.
- Chroma vector DB: insightiq/knowledge/chroma_store.py.
- Hugging Face LLM client: insightiq/llm/huggingface_client.py.
- Dockerfile: docker/Dockerfile.
