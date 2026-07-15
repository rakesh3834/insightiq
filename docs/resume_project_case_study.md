# InsightIQ — Data Scientist Case Study

> Positioning doc for resume + interviews. Optimised for **Data Scientist** roles (≈1 YoE).
> Lead with the modeling + experimentation spine; the LLM/agent layer is a supporting story, not the headline.

---

## Resume title

**Decision Intelligence Platform — Predictive Modeling · Experimentation · Product Analytics**

## One-line version

Built an end-to-end decision-intelligence platform on 170K+ e-commerce records that predicts order-cancellation risk, runs A/B experiment readouts, and converts model output into **calibrated, dollar-quantified** launch/intervene decisions — served via FastAPI and a Next.js dashboard.

---

## Resume bullets (quantified, DS-focused)

Use 3–5 of these. Every one has a number and a defensible story behind it.

**Modeling**
- Built an order-cancellation risk model on 20K orders (15K/5K stratified split): compared 5 classifiers (Logistic Regression, KNN, Random Forest, HistGradientBoosting, XGBoost) by **5-fold cross-validated ROC-AUC**, selecting Logistic Regression (**0.74 ± 0.01 CV AUC**) as the best speed/accuracy trade-off.
- Improved probability reliability by **isotonic-calibrating** the model — cut the **Brier score 21%** (0.20 → 0.16) — so predicted probabilities can be read as true cancellation rates by downstream ops.
- Chose the decision threshold from a **precision/recall/F1 sweep** rather than the naive 0.5 cut; the F1-optimal **0.25** threshold (imbalanced positive class) recovers **65% of cancellations at 42% precision**.

**Feature selection**
- Ran a **5-method feature-selection study** (mutual-information filter, L1/Lasso embedded, RFECV, forward + backward wrappers) with per-feature consensus voting; showed a **5-feature subset matches full-set AUC (0.748 vs 0.749)**, and that the univariate MI filter underperforms (0.689) by missing multivariate signal.

**Experimentation & decision science**
- Implemented **two-proportion z-tests** on per-arm conversion counts for 24 A/B experiments (**10 significant at p<0.05**), feeding ship / rollback / iterate readouts.
- Translated model output into a **business case**: at the operating threshold the model recovers **~$177K GMV per 5K-order window** (847 caught × $596 AOV × 35% assumed save-rate), framing the threshold as a lever between recovered revenue and review cost.

**Breadth (ML + engineering)**
- Shipped supporting models — IsolationForest anomaly detection, KMeans segmentation, Holt-Winters forecasting (95% CI), DistilBERT sentiment, and c-TF-IDF complaint clustering over MiniLM embeddings — all with offline fallbacks, exposed through a **FastAPI** service and a **Next.js** analytics dashboard.

---

## Three "hero" components — go deep on these

Interviewers will probe *something*. Be ready to whiteboard these three; speak to everything else at altitude.

1. **Cancellation model, model→decision arc.** CV selection → calibration (Brier 0.20→0.16) → F1-optimal threshold (0.25) → recovered-GMV. This single arc demonstrates the full data-scientist loop: model, validate, calibrate, choose an operating point, quantify impact.
2. **Feature selection.** Filter vs embedded vs wrapper families disagree; wrappers match full-set AUC with fewer features; MI filter misses interactions. Shows you understand *why* methods differ, not just how to call them.
3. **Experimentation + decision layer.** Real z-tests → significance → the orchestrated launch/iterate/rollback/investigate decision. Shows product/decision-science judgment, which is what separates a DS from a pure ML engineer.

---

## The synthetic-label framing — SAY THIS FIRST

The public e-commerce `order_status` is randomly assigned (no learnable signal), so the model can't be trained on it directly. **Own this before anyone asks:**

> "The public label was noise, so I engineered a *documented* synthetic risk process from genuine drivers — order value, account tenure, engagement, quantity, late-night impulse — with irreducible Bernoulli noise so the achievable AUC is realistic (~0.74, not a fake 1.0). I then confirmed the model's permutation importances **recover those exact drivers**. The label is synthetic; the **methodology** — feature engineering, CV selection, calibration, thresholding, feature selection, persistence, serving — is production-shaped."

This reframes a weakness as evidence you understand data-generating processes and honest evaluation. Interviewers respect it far more than a suspiciously perfect metric.

---

## Tech stack (accurate — keep it current)

Python · pandas · scikit-learn · XGBoost · statsmodels · sentence-transformers (MiniLM) · Chroma (vector store) · LangGraph · Hugging Face Inference (Llama-3.1-8B-Instruct) · FastAPI · **SQLite (single source of truth)** · Next.js / TypeScript / Recharts.

> ⚠️ Do **not** say DuckDB — it was removed; SQLite is the warehouse. The old case-study draft listed it; that's a factual trap.

---

## Role fit

- **Data Scientist:** feature engineering, model comparison + CV, calibration, thresholding, feature selection, anomaly detection, forecasting, clustering, evaluation.
- **Decision Scientist / Product DS:** KPI design, A/B hypothesis testing, root-cause analysis, launch decision memos, dollar-quantified trade-offs.
- **Applied ML / AI Engineer (secondary):** FastAPI serving, RAG retrieval, LangGraph agents, cost-optimization patterns.

---

## ATS keywords (trimmed to DS-relevant)

Machine Learning, Classification, Logistic Regression, XGBoost, Random Forest, Cross-Validation, Model Evaluation, ROC-AUC, Precision/Recall, Probability Calibration, Isotonic Regression, Brier Score, Decision Threshold, Feature Selection, Feature Engineering, Class Imbalance, A/B Testing, Hypothesis Testing, Two-Proportion Z-Test, Anomaly Detection, Time-Series Forecasting, Clustering, Segmentation, NLP, Sentiment Analysis, Topic Modeling, Embeddings, RAG, Python, scikit-learn, pandas, FastAPI, SQL, Data Pipeline, Product Analytics, Decision Science, Experimentation.
