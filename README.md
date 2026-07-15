# InsightIQ — Decision Intelligence Platform

> Predictive modeling · experimentation · product analytics — turned into **calibrated, dollar-quantified product decisions.**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikitlearn&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-Dashboard-000000?logo=nextdotjs&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agents-1C3C3C)
![Tests](https://img.shields.io/badge/tests-13%20passing-brightgreen)

InsightIQ takes raw e-commerce data (users, orders, events, reviews) and answers the question every product team faces: *a metric moved — do we **launch, iterate, roll back, or investigate?*** It does this with a real data-science spine — a calibrated cancellation-risk model, A/B experiment readouts, forecasting, and anomaly detection — wrapped in a LangGraph decision layer, served through a FastAPI backend and a Next.js dashboard.

It is deliberately **not** chatbot-first or dashboard-first. The headline artifact is a **decision** backed by evidence, a recommendation, and a dollar figure.

---

## 🌐 Try it live

Deploy your own instance in ~2 minutes (free tier, no token needed — runs on deterministic fallbacks):

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/rakesh3834/insightiq)

Once up, the API is at `https://<your-app>.onrender.com` — open **`/docs`** for interactive Swagger where you can test every endpoint, including `POST /model/predict` (score an order's cancellation risk) and `GET /model/evaluation` (the full model report). See [Deployment](#-deployment) below for the frontend.

---

## 🎯 Headline results — cancellation-risk model

A supervised pipeline that scores each order's cancellation probability so ops can intervene *before* revenue is lost. The full data-scientist loop — **model → validate → calibrate → choose an operating point → quantify impact.**

**Model selection by 5-fold cross-validated ROC-AUC** (robust to split luck):

| Model | CV ROC-AUC |
|---|---|
| **Logistic Regression** ✅ *(selected)* | **0.741 ± 0.013** |
| Random Forest | 0.736 |
| HistGradientBoosting | 0.735 |
| XGBoost | 0.719 |
| K-Nearest Neighbors | 0.710 |

| What | Result | Why it matters |
|---|---|---|
| **Probability calibration** (isotonic) | Brier **0.204 → 0.162** (−21%) | Predicted probabilities can be read as true cancellation rates |
| **Operating threshold** (max-F1, not naive 0.5) | **0.25** → recall **0.65**, precision **0.42** | Positive class is only 26% — the threshold is tuned to the imbalance |
| **Feature selection** (5 methods + consensus vote) | 5-feature subset ≈ full-set AUC (**0.748 vs 0.749**) | Half the features, same performance; MI filter alone underperforms (0.689) |
| **Business impact** | **~$177K recovered GMV** per 5K-order window vs **$274K** leaked if no action | The threshold is a lever: recovered revenue ⇄ review cost |

> **On the data:** the public `order_status` is randomly assigned (no learnable signal), so the cancellation label is a *documented synthetic risk process* built from genuine drivers (order value, tenure, engagement, late-night impulse) plus irreducible noise — the model's permutation importances recover those exact drivers. **The label is synthetic; the methodology is production-shaped.** See [`docs/interview_qa.md`](docs/interview_qa.md).

---

## 🖼️ Screenshots

> Add PNGs to `docs/screenshots/` with these names and they'll render here.

| Risk Model | Calibration & Threshold | Decision Dashboard |
|---|---|---|
| ![Risk model](docs/screenshots/risk-model.png) | ![Calibration](docs/screenshots/calibration.png) | ![Dashboard](docs/screenshots/dashboard.png) |

---

## 🏗️ Architecture

```
                 ecommerce_dataset/ (users, orders, events, reviews, order_items, products)
                                    │
                        ┌───────────▼───────────┐
                        │   run_pipeline()       │  batch: 14 steps → 25+ artifacts
                        │   (insightiq/)         │
                        └───────────┬───────────┘
        ┌──────────────┬───────────┼────────────┬─────────────────┐
        ▼              ▼           ▼             ▼                 ▼
   ML models     A/B z-tests   Forecasting   Review NLP     LangGraph agents
   • cancel risk • two-prop    • Holt-Winters • DistilBERT   Metrics→Experiment
     (CV+calib     z-test        95% CI         sentiment    →CustomerVoice
     +threshold)  • ship/roll   • anomalies    • c-TF-IDF    →ReleaseIncident
   • KMeans seg     back          (IsoForest)   clustering        │
   • feat. select                                                 ▼
        │                                              DecisionOrchestrator
        └──────────────► artifacts/ ◄────────────────  launch/iterate/rollback
                              │                                   │
                 ┌────────────▼────────────┐          SQLite (single source of truth)
                 │  FastAPI  (backend/)     │          + Chroma vector store
                 │  26 endpoints            │
                 └────────────┬────────────┘
                              ▼
                 Next.js dashboard (frontend/)  ·  Streamlit demo (demo/)
```

**Two request flows:**
- `POST /chat` — fast static reader over precomputed artifacts (no ML at request time).
- `POST /ask` — **agentic**: question → LLM intent → Chroma retrieval → 4 LangGraph agents → rule-based orchestrator → LLM-synthesized answer with citations.

Every ML/LLM component has an **offline fallback** (hash embeddings, lexicon sentiment, deterministic decisions), so the whole pipeline runs with no network or API token.

---

## 🚀 Quickstart

**Backend + pipeline**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # optional: add HF_TOKEN for real LLM/embeddings

python scripts/run_all.py       # runs the pipeline → writes artifacts/
python scripts/start_api.py     # FastAPI at http://localhost:8000  (docs at /docs)
```

**Frontend dashboard**
```bash
cd frontend
npm install
npm run dev                     # http://localhost:3000
```

**Run fully offline (no HF token):** set `INSIGHTIQ_USE_HF_EMBEDDINGS=false` and `INSIGHTIQ_USE_HF_SENTIMENT=false` in `.env`.

**Tests**
```bash
pytest                          # 13 passing — data contracts + ML models
```

---

## 🔌 Selected API endpoints

| Endpoint | Returns |
|---|---|
| `GET /model/evaluation` | Leaderboard (CV AUC), calibration, threshold sweep, feature importance, business case |
| `GET /model/feature-selection` | 5-method comparison + consensus vote + subset AUC |
| `POST /model/predict` | Score one order → probability, risk band, flagged, operating threshold |
| `POST /ask` | Agentic decision answer with evidence + citations |
| `GET /experiments/decisions` | A/B z-test readouts → ship / rollback / iterate |
| `GET /metrics/summary` · `/metrics/funnel` | KPIs and funnel |
| `GET /recommendations/decision` | Orchestrated launch/iterate/rollback/investigate |

Full list at `/docs` (FastAPI Swagger UI).

---

## 🧠 ML / DS stack

- **Supervised:** Logistic Regression, KNN, Random Forest, HistGradientBoosting, XGBoost — compared by cross-validated ROC-AUC, isotonic-calibrated, thresholded.
- **Feature selection:** mutual-information filter, L1/Lasso, RFECV, forward + backward wrappers, consensus vote.
- **Unsupervised:** KMeans segmentation, IsolationForest anomalies, c-TF-IDF complaint clustering over MiniLM embeddings.
- **Stats / time series:** two-proportion z-tests (A/B), Holt-Winters forecasting with 95% CI.
- **NLP / retrieval:** DistilBERT sentiment (SST-2), sentence-transformers embeddings, Chroma vector store.
- **Agents / LLM:** LangGraph `StateGraph` (4 agents), Hugging Face `InferenceClient` (Llama-3.1-8B-Instruct).

---

## 📂 Project structure

```
insightiq/       core AI logic — pipeline, ml/, agents/, graph/, knowledge/, llm/
backend/         FastAPI service (26 endpoints)
frontend/        Next.js + TypeScript dashboard (9 pages, Recharts)
artifacts/       generated outputs (CSV/JSON/MD) + persisted model + SQLite warehouse
data_synthetic/  synthesized PM context (release notes, A/B tests, incidents, flags)
ecommerce_dataset/  source-of-truth CSVs
docs/            architecture, PRD, case study, monitoring, interview Q&A
tests/           pytest suites (data contracts + ML)
```

---

## 📚 Docs

- [Resume / project case study](docs/resume_project_case_study.md) — positioning + quantified bullets
- [Interview Q&A / objection handling](docs/interview_qa.md) — how each decision is defended
- [Productionization & monitoring](docs/productionization_and_monitoring.md) — serving, drift, retraining
- [Architecture](docs/architecture.md) · [Product requirements](docs/product_requirements.md) · [Decision-intelligence design](docs/decision_intelligence_architecture.md)

---

## 🚢 Deployment

| Service | Host | Notes |
|---|---|---|
| **Backend API** | Render (`deployment/render.yaml`) | One-click button above. Binds `$PORT`, `/health` check, rebuilds artifacts on boot. Runs tokenless by default. |
| **Frontend** | Vercel | Import `frontend/`, set `NEXT_PUBLIC_API_URL` to your Render API URL. |
| **Container** | Docker | `docker compose up --build` → API on `:8000`. |

To enable the real LLM + HF embeddings/sentiment on a deployment, add `HF_TOKEN` and set `INSIGHTIQ_USE_HF_EMBEDDINGS` / `INSIGHTIQ_USE_HF_SENTIMENT` to `true`. If you deploy the frontend on a different origin than the API, enable CORS for that origin on the backend.

## 🛠️ Tech stack

Python · pandas · scikit-learn · XGBoost · statsmodels · sentence-transformers · Chroma · LangGraph · Hugging Face Inference · FastAPI · **SQLite (single source of truth)** · Next.js / TypeScript / Recharts · Docker · Render.

## License

MIT — see `LICENSE` (add one if not present).
