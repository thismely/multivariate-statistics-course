#!/usr/bin/env python3
"""Offline logistic-regression laboratory with a leak-safe preprocessing pipeline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, log_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 6601
LAB_ID = "logistic"
FEATURES = [f"predictor_{i}" for i in range(1, 7)]


def make_data() -> tuple[pd.DataFrame, np.ndarray]:
    x, y = make_classification(
        n_samples=260,
        n_features=len(FEATURES),
        n_informative=4,
        n_redundant=1,
        n_classes=2,
        weights=[0.58, 0.42],
        class_sep=1.25,
        random_state=SEED,
    )
    return pd.DataFrame(x, columns=FEATURES), y


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    data, target = make_data()
    train_idx, test_idx = train_test_split(
        np.arange(len(target)), test_size=0.25, random_state=SEED, stratify=target
    )
    model = make_pipeline(
        StandardScaler(), LogisticRegression(max_iter=2000, solver="lbfgs", random_state=SEED)
    )
    model.fit(data.iloc[train_idx][FEATURES], target[train_idx])
    predicted = model.predict(data.iloc[test_idx][FEATURES])
    probability = model.predict_proba(data.iloc[test_idx][FEATURES])[:, 1]
    data.assign(synthetic_class=target).to_csv(args.output_dir / f"{LAB_ID}_data.csv", index=False)
    pd.DataFrame({"actual": target[test_idx], "predicted": predicted, "probability_1": probability}).to_csv(
        args.output_dir / f"{LAB_ID}_predictions.csv", index=False
    )
    classifier = model[-1]
    result = {
        "lab_id": LAB_ID,
        "seed": SEED,
        "split": {"test_size": 0.25, "stratified": True, "random_state": SEED},
        "preprocessing": "StandardScaler is fitted on training rows only inside a Pipeline",
        "test_metrics": {
            "accuracy": float(accuracy_score(target[test_idx], predicted)),
            "roc_auc": float(roc_auc_score(target[test_idx], probability)),
            "log_loss": float(log_loss(target[test_idx], model.predict_proba(data.iloc[test_idx][FEATURES]))),
            "confusion_matrix_labels_0_1": confusion_matrix(target[test_idx], predicted, labels=[0, 1]).tolist(),
        },
        "standardized_odds_ratios": {
            name: float(np.exp(value)) for name, value in zip(FEATURES, classifier.coef_[0])
        },
        "checks": {
            "train_rows": int(len(train_idx)),
            "test_rows": int(len(test_idx)),
            "no_row_overlap": bool(set(train_idx).isdisjoint(set(test_idx))),
            "probability_in_unit_interval": bool(np.all((probability >= 0) & (probability <= 1))),
        },
    }
    (args.output_dir / f"{LAB_ID}_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
