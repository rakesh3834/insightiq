# Productionization & Monitoring — Cancellation Risk Model

> Answers the near-guaranteed interview question: *"You deployed a model — how do you know it's still working?"*
> This documents the serving design that exists today and the monitoring/retraining plan for a real deployment.

---

## 1. Serving architecture (what exists today)

- **Train-once, reuse-forever.** `train_cancellation_model(force=False)` trains, calibrates, and persists the winning pipeline to `artifacts/models/cancellation_model.joblib`; subsequent runs load the cached model and evaluation report instead of retraining.
- **The served artifact is the calibrated pipeline** — `CalibratedClassifierCV` wrapping `StandardScaler + OneHotEncoder → LogisticRegression`. Preprocessing travels *inside* the pipeline, so training and inference apply identical transforms (no train/serve skew).
- **Inference path:** `POST /model/predict` → `predict()` loads the bundle, applies the pipeline, returns `cancellation_probability`, `risk_band`, `flagged`, and the `operating_threshold`. Single-order latency is <1 ms; no LLM/network in the request path.
- **The operating threshold is persisted with the model**, so the serving decision boundary is versioned alongside the weights, not hard-coded in the API.

## 2. When to retrain

Retrain on the earliest trigger, not a fixed calendar:

| Trigger | Signal |
|---|---|
| **Performance decay** | Rolling ROC-AUC or recall on labeled outcomes drops below a floor (e.g. AUC < 0.70). |
| **Calibration drift** | Brier score or reliability-curve gap widens (probabilities stop matching observed rates). |
| **Input drift** | Feature distributions shift materially (see §3). |
| **Label/base-rate shift** | The cancellation base rate moves (e.g. 26% → 32%) — the threshold and economics need re-derivation. |
| **Scheduled floor** | A monthly retrain as a backstop even if no trigger fires. |

## 3. Drift monitoring (what to watch, and why)

- **Feature drift (input):** track **PSI / population-stability** or a KS test per feature (`order_value`, `account_age_days`, `n_events`, `order_hour`, …). PSI > 0.2 on a top-importance feature = investigate. This catches upstream data changes *before* they show up as accuracy loss.
- **Prediction drift (output):** monitor the distribution of predicted probabilities and the **flag rate** (currently ~40%). A sudden jump means the population or a feature pipeline changed.
- **Performance + calibration (once labels arrive):** cancellations resolve with a lag, so compute **recall and Brier score on matured orders** on a rolling window. **Watch recall and calibration, not accuracy** — accuracy is misleading on a 26%-positive imbalanced problem (a "never cancel" model scores 74%).
- **Threshold health:** re-run the precision/recall/F1 sweep on fresh labeled data; if the F1-optimal point moves off 0.25, re-set the operating threshold (it's a business lever, not a constant).

## 4. The metric hierarchy (say this)

1. **Recall** — missing a cancellation = lost revenue you could have saved. Primary.
2. **Calibration (Brier / reliability)** — ops act on the *probability*, so it must be honest.
3. **Precision** — governs review workload / false-alarm cost.
4. **Accuracy** — deliberately *not* a headline metric here (imbalance makes it vanity).

## 5. Rollback & safety

- Model artifacts are versioned; a bad retrain rolls back to the previous `joblib` bundle + its threshold.
- The pipeline degrades gracefully: if the model or its dependencies fail (e.g. XGBoost/`libomp` missing on macOS), training is caught and logged, and the rest of the pipeline still produces artifacts.

## 6. Honest current-state gaps (for a real deployment)

Be upfront that this is a portfolio build, not a live system:
- **Label is synthetic** — a real deployment needs the true cancellation outcome joined back on a lag to compute live metrics.
- **No live drift dashboard yet** — PSI/monitoring described here is the *plan*; today evaluation is batch, written to `model_evaluation.json`.
- **No automated retraining pipeline / CI** — retrain is a manual `force=True` run.
- **Single-node serving** — fine for a demo; a real system would containerize the model behind an autoscaled endpoint with a feature store to guarantee train/serve parity.

Naming these unprompted signals maturity — you know the difference between a demo and production.
