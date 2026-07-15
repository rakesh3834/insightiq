"""Feature-selection comparison for the cancellation-risk model.

Runs five selection strategies over the engineered features and compares which
features each keeps, plus the cross-validated ROC-AUC of a model trained on each
selected subset vs the full feature set:

  • Filter   — Mutual Information (model-free dependence with the target)
  • Embedded — L1 (Lasso) Logistic Regression via SelectFromModel
  • Wrapper  — RFECV (recursive elimination, CV-tuned)
  • Wrapper  — Sequential Forward Selection (SFS)
  • Wrapper  — Sequential Backward Selection (SBS)

A per-feature "vote" (how many methods keep it) yields a robust consensus set.
The report is persisted to artifacts/feature_selection.json (train-once / reuse).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from insightiq.ml.cancellation_model import (
    ARTIFACTS, CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES, RANDOM_STATE, TARGET,
    build_feature_frame, _realistic_cancellation_label,
)

FS_PATH = ARTIFACTS / "feature_selection.json"
CV_FOLDS = 4
SAMPLE_N = 5000  # subsample for the (CV-heavy) wrapper searches — standard practice


def _design_matrix(df: pd.DataFrame):
    """Scale numerics + one-hot the categorical → dense matrix + clean names."""
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    pre = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])
    X = pre.fit_transform(df[FEATURES])
    X = np.asarray(X.todense()) if hasattr(X, "todense") else np.asarray(X)
    names = [n.split("__", 1)[-1] for n in pre.get_feature_names_out()]
    return X, names


def run_feature_selection(frames: dict[str, pd.DataFrame], force: bool = False) -> dict[str, Any]:
    if FS_PATH.exists() and not force:
        return json.loads(FS_PATH.read_text())

    from sklearn.base import clone
    from sklearn.feature_selection import (
        RFECV, SelectFromModel, SequentialFeatureSelector, mutual_info_classif,
    )
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score

    df = build_feature_frame(frames)
    df[TARGET] = _realistic_cancellation_label(df)
    if len(df) > SAMPLE_N:
        df = df.sample(n=SAMPLE_N, random_state=RANDOM_STATE)
    X, names = _design_matrix(df)
    y = df[TARGET].to_numpy()

    estimator = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE)

    # ── Filter: Mutual Information (keep features with MI above the mean) ──
    mi = mutual_info_classif(X, y, random_state=RANDOM_STATE)
    mi_mask = mi >= mi.mean()

    # ── Embedded: L1 (Lasso) logistic regression ──
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)  # penalty= API churn across sklearn versions
        l1 = SelectFromModel(
            LogisticRegression(penalty="l1", solver="liblinear", class_weight="balanced", random_state=RANDOM_STATE)
        ).fit(X, y)
    l1_mask = l1.get_support()

    # ── Wrapper: RFECV ──
    rfecv = RFECV(clone(estimator), step=1, cv=CV_FOLDS, scoring="roc_auc", n_jobs=-1).fit(X, y)
    rfe_mask = rfecv.support_

    # ── Wrapper: Sequential Forward / Backward Selection ──
    sfs = SequentialFeatureSelector(
        clone(estimator), n_features_to_select="auto", tol=1e-3, direction="forward",
        scoring="roc_auc", cv=CV_FOLDS, n_jobs=-1,
    ).fit(X, y)
    sfs_mask = sfs.get_support()
    sbs = SequentialFeatureSelector(
        clone(estimator), n_features_to_select="auto", tol=1e-3, direction="backward",
        scoring="roc_auc", cv=CV_FOLDS, n_jobs=-1,
    ).fit(X, y)
    sbs_mask = sbs.get_support()

    method_masks = {
        "Mutual Information": mi_mask,
        "L1 (Lasso)": l1_mask,
        "RFECV": rfe_mask,
        "Forward SFS": sfs_mask,
        "Backward SBS": sbs_mask,
    }

    def subset_auc(mask: np.ndarray) -> float:
        if mask.sum() == 0:
            return 0.0
        scores = cross_val_score(clone(estimator), X[:, mask], y, cv=CV_FOLDS, scoring="roc_auc", n_jobs=-1)
        return round(float(scores.mean()), 4)

    # Per-feature selection matrix + consensus vote.
    selection = []
    for i, name in enumerate(names):
        votes = int(sum(bool(m[i]) for m in method_masks.values()))
        selection.append({
            "feature": name,
            "mi_score": round(float(mi[i]), 4),
            "mutual_information": bool(mi_mask[i]),
            "l1": bool(l1_mask[i]),
            "rfecv": bool(rfe_mask[i]),
            "sfs": bool(sfs_mask[i]),
            "sbs": bool(sbs_mask[i]),
            "votes": votes,
        })
    selection.sort(key=lambda d: (d["votes"], d["mi_score"]), reverse=True)

    subset_scores = [{"method": "Full feature set", "n_features": len(names), "roc_auc": subset_auc(np.ones(len(names), bool))}]
    for method, mask in method_masks.items():
        subset_scores.append({"method": method, "n_features": int(mask.sum()), "roc_auc": subset_auc(mask)})

    consensus = [s["feature"] for s in selection if s["votes"] >= 3]

    report = {
        "n_samples": int(len(df)),
        "cv_folds": CV_FOLDS,
        "methods": list(method_masks.keys()),
        "selection": selection,
        "subset_auc": subset_scores,
        "consensus_features": consensus,
        "note": "Consensus = kept by ≥3 of 5 methods. Wrappers use Logistic Regression with balanced class weights.",
    }
    FS_PATH.write_text(json.dumps(report, indent=2))
    return report
