# Product Requirements

## Business Problem

Product teams often make launch decisions from disconnected tools: event analytics, dashboards, SQL workspaces, customer reviews, release notes, and stakeholder opinions. InsightIQ unifies those signals into an evidence-backed decision workflow so teams can explain what changed, why it changed, and what to do next.

## Target Users

- Product managers deciding whether to ship, iterate, or roll back.
- Data scientists validating metric changes and modeling user behavior.
- Product analysts writing SQL and building dashboard extracts.
- Engineering managers connecting incidents and release changes to product KPIs.
- Executives who need a concise decision memo.

## Pain Points

- KPI changes are visible, but root cause is slow to prove.
- Reviews and release notes are rarely connected to quantitative trends.
- Product decisions rely on manually copied charts and fragmented narratives.
- Analysts repeat the same SQL and analysis work across launch reviews.
- AI summaries can hallucinate when not grounded in warehouse data.

## MVP

The MVP ingests ecommerce CSVs, builds a SQLite/DuckDB warehouse, indexes evidence in Chroma, runs LangGraph decision orchestration, analyzes reviews, synthesizes release-note and experiment context, calls a Hugging Face open-source LLM when configured, and exports decision artifacts.

Included:

- Mixpanel-style funnel and event analytics.
- Tableau-style dashboard extracts.
- SQL validation queries.
- Data science models for anomaly detection, forecasting, segmentation, sentiment, and topics.
- Review intelligence and release-note impact analysis.
- Presentation and decision memo generation.
- Evaluation report with latency, row coverage, SQL checks, and artifact completeness.

Deferred:

- Multi-tenant authentication.
- Real SaaS billing.
- Live Mixpanel/Tableau connectors.
- Managed vector database.
- Production LLM provider integration.

## KPIs

- North Star Metric: percentage of weekly product decisions backed by complete quantitative and qualitative evidence.
- Activation: first successful dataset ingestion and decision memo generated.
- Engagement: weekly decision workflows completed.
- Quality: recommendation acceptance rate.
- Trust: hallucination rate and SQL validation pass rate.
- Efficiency: analyst hours saved per launch review.

## Scalability Challenges

- Joining high-volume event streams with orders and reviews.
- Cost control for embeddings and LLM summaries.
- Freshness guarantees across batch dashboards and streaming incidents.
- Permission boundaries for product, finance, and customer data.
- Evaluation of generated recommendations across many teams and domains.

## Edge Cases

- Missing product or user dimensions.
- Orders with cancelled or processing states.
- Sparse reviews for new products.
- Event spikes caused by bots or tracking bugs.
- Release notes without measurable KPI movement.
- Conflicting quantitative and qualitative signals.
- Duplicate events or late-arriving order updates.

## Resume Impact

This project demonstrates end-to-end AI product engineering: data warehousing, analytics engineering, ML modeling, agent architecture, production API design, evaluation, cost-aware AI workflows, and executive decision automation.
