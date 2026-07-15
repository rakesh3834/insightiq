# Decision Intelligence Architecture

InsightIQ is not a chatbot and not a dashboard project. It is an AI Decision Intelligence Platform.

## Core Workflow

```text
Business Question
  -> Metrics Evidence
  -> Experiment Evidence
  -> Customer Voice Evidence
  -> Release and Incident Evidence
  -> Root Cause Reasoning
  -> Recommendation
  -> Decision Memo
  -> Evaluation
```

## Why This Architecture

Product decisions require structured and unstructured evidence. SQL can explain what moved, reviews and documents explain customer context, experiments estimate causal impact, and incidents/releases explain operational context. The orchestrator combines these signals into a recommendation with explicit risks and next actions.

## Runtime Layers

- Data layer: ecommerce CSVs plus synthetic product-management context.
- Warehouse layer: SQLite for portability, DuckDB when available, PostgreSQL-compatible production design.
- Knowledge layer: Chroma persistent vector DB with local hash embeddings by default and replaceable Hugging Face/sentence-transformer embeddings.
- Agent layer: LangGraph `StateGraph` orchestration with deterministic agent tools.
- Decision layer: action selection across launch, iterate, rollback, and investigate.
- LLM layer: Hugging Face `InferenceClient` calling an open-source chat model when `HF_TOKEN` is configured.
- Evaluation layer: evidence coverage, confidence, actionability, and artifact completeness.

## Agents

- Metrics Agent: reads KPI and funnel artifacts.
- Experiment Agent: evaluates p-values, lift, and rollout recommendations.
- Customer Voice Agent: retrieves review evidence and summarizes pain themes.
- Release Incident Agent: retrieves release, feature, and incident context.
- Decision Orchestrator: ranks risk and opportunity evidence into a recommendation.

## Alternatives Considered

- Chatbot-first: easier to demo but too generic and weaker for interviews.
- Dashboard-first: useful for analysts but does not show AI reasoning.
- Script-only analytics: useful for exploration but weaker as a production portfolio signal.
- Fully LLM-driven agents: impressive but harder to evaluate and more prone to hallucination.

The chosen approach uses deterministic evidence-first agents with LLM-ready boundaries. This is stronger for interviews because every claim can be traced to data.

## Scalability Plan

- Replace local hash embeddings with sentence-transformers or Hugging Face embedding endpoints.
- Replace SQLite with PostgreSQL for app metadata and DuckDB/cloud warehouse for analytics.
- Cache embeddings and SQL results.
- Make long-running decisions background jobs.
- Add LangGraph checkpointing for resumable stateful orchestration.
- Track decision quality with MLflow or a lightweight evaluation table.
