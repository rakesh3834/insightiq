# InsightIQ — Interview Q&A / Objection Handling

> Rehearse these out loud. Numbers are current as of the latest pipeline run.
> Golden rule: for anything you can't defend in depth, say "at a high level…" and pivot to a hero component.

---

## 30-second pitch

> "InsightIQ turns raw e-commerce data into product decisions. The data-science core is an order-cancellation risk model — I compare five classifiers with cross-validated AUC, calibrate the winner's probabilities, and pick a decision threshold from a precision/recall sweep, then translate that into recovered GMV. Around it sits A/B experiment readouts, forecasting, anomaly detection, and a decision layer that recommends launch / iterate / rollback / investigate. It's served through a FastAPI backend and a Next.js dashboard."

---

## The one they'll ask first

**Q: Is this real data? Isn't the cancellation label made up?**
> "The public `order_status` is randomly assigned — no learnable signal — so I couldn't train on it honestly. I engineered a *documented* synthetic risk label from genuine drivers (order value, account tenure, engagement, quantity, late-night impulse) plus irreducible noise, so the achievable AUC is realistic at ~0.74, not a fake 1.0. I then verified the model's permutation importances recover those exact drivers. The label is synthetic; the methodology — CV selection, calibration, thresholding, feature selection, serving — is production-shaped. On real data I'd swap the label for the true outcome and the pipeline is unchanged."

---

## Modeling

**Q: Why Logistic Regression over XGBoost?**
> "I selected by 5-fold CV ROC-AUC, and LogReg won (0.741 ± 0.013) — the tree models were within noise (RF 0.736, HistGB 0.735, XGBoost 0.719). With comparable AUC I prefer the simpler model: it's interpretable (signed coefficients), calibrates cleanly, trains and scores fast, and has less overfitting risk on 15K rows. If a tree model had clearly won on CV, I'd have taken it."

**Q: Why cross-validation instead of a single train/test split?**
> "A single split can be lucky or unlucky. 5-fold CV gives a mean *and* a std (±0.013 here), so I know the model ranking is stable, not an artifact of one partition. I still report final metrics on a held-out test set the CV never touched."

**Q: What is calibration and why did you add it?**
> "A model can rank well (good AUC) but output probabilities that don't match reality — LogReg with balanced class weights inflates them. Since ops act on the *probability* (a 0.8 should mean ~80% cancel), I isotonic-calibrated the model, which cut the Brier score 21% (0.20→0.16) and pulled the reliability curve onto the diagonal. Calibrated probabilities are what make the score operational."

**Q: Why is your threshold 0.25 and not 0.5?**
> "0.5 is only right for a balanced problem. Cancellations are ~26% of orders, so I swept thresholds and picked the F1-optimal point, which lands at 0.25. That flags ~40% of orders and catches 65% of cancellations at 42% precision. The threshold is a business lever — lower it to recover more revenue with more manual reviews, raise it to cut review cost."

**Q: Your precision is only 0.42 — isn't that bad?**
> "For this use case, no. A false positive costs one support/verification touch; a false negative costs a whole order's revenue. So I optimise recall-leaning, and the economics still net out positive: ~$177K recovered vs the cost of reviewing 2,017 orders per 5K window. If review capacity were the constraint, I'd raise the threshold and trade recall for precision — the sweep makes that an explicit dial."

**Q: How did you handle class imbalance?**
> "Balanced class weights / `scale_pos_weight` in the models, stratified splits and stratified CV, and evaluation on recall/F1/AUC/Brier rather than accuracy — accuracy is a vanity metric at 26% base rate since 'never cancel' already scores 74%."

---

## Feature selection

**Q: What did the feature-selection study show?**
> "I ran five methods across the filter/embedded/wrapper families with consensus voting. A 5-feature subset from forward selection matched the full-set AUC (0.748 vs 0.749) — so I can more than halve the features with no accuracy loss. The univariate MI filter underperformed (0.689) because it scores features independently and misses multivariate interactions. The lesson: method family matters, and wrappers respect feature interactions that filters can't see."

---

## Experimentation & product

**Q: How does the A/B testing work?**
> "Two-proportion z-tests on per-arm conversion counts — 10 of 24 experiments were significant at p<0.05. Those readouts feed ship/rollback/iterate recommendations. It's real inferential statistics computed from counts, not pre-set p-values."

**Q: How did you get the business-impact number?**
> "From the confusion matrix at the operating threshold: caught cancellations × average order value × an assumed 35% intervention save-rate = ~$177K recovered per 5K-order test window, against $274K still leaking if we do nothing. The save-rate is a documented assumption I'd replace with a measured rate once there's intervention A/B data — I'm explicit that it's an assumption."

**Q: Why a decision layer at all — why not just a model?**
> "Because a probability isn't a decision. The value is in choosing an *action* — launch, iterate, rollback, investigate — under conflicting signals. That's the product/decision-science judgment layer, and it's what turns a model into something a PM can use."

---

## Engineering / deployment

**Q: How is the model served, and how would you monitor it?**
> "Train-once: the calibrated pipeline (preprocessing inside, so no train/serve skew) is persisted to disk with its threshold and loaded for <1ms inference behind a FastAPI endpoint. For monitoring I'd track PSI on input features, the prediction/flag-rate distribution, and rolling recall + Brier on matured labels — watching recall and calibration, not accuracy. Retraining triggers on performance decay, calibration drift, input drift, or base-rate shift." *(See `productionization_and_monitoring.md`.)*

**Q: How would you take this to real production / scale?**
> "Join the true cancellation outcome back on a lag for live metrics; put the model behind a containerized autoscaled endpoint; add a feature store to guarantee train/serve parity; and automate retraining in CI with the drift triggers above. The modeling methodology stays the same — it's the surrounding infra that hardens."

---

## Reflection

**Q: What are the project's limitations?**
> "Three, honestly: the cancellation label is synthetic (public label was noise); monitoring is currently batch, not a live drift dashboard; and I didn't do heavy hyperparameter tuning because CV showed the models were within noise of each other, so calibration and thresholding were higher-leverage. I'd rather be right about what matters than gold-plate."

**Q: What would you do differently / next?**
> "Add SHAP for per-order reason codes so ops get a 'why this order was flagged' string — I scoped it but deferred it since global importance on a linear model is already close to the coefficients. On real data I'd also A/B test the interventions themselves to measure the true save-rate."

**Q: What did you learn?**
> "That the model is the easy 20%. The hard, valuable 80% is honest evaluation (CV, calibration), picking an operating point that reflects the business cost asymmetry, and translating a probability into a decision and a dollar number."
