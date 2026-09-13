#!/usr/bin/env python3
"""Offline LDA/QDA discriminant-analysis laboratory with a leak-safe split."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 6401
LAB_ID = "discriminant"
FEATURES = [f"financial_ratio_{i}" for i in range(1, 7)]


def make_data() -> tuple[pd.DataFrame, np.ndarray]:
    x, y = make_classification(
        n_samples=240,
        n_features=len(FEATURES),
        n_informative=4,
        n_redundant=1,
        n_repeated=0,
        n_classes=3,
        n_clusters_per_class=1,
        class_sep=1.7,
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
    data.assign(synthetic_class=target).to_csv(args.output_dir / f"{LAB_ID}_data.csv", index=False)
    outputs: dict[str, object] = {}
    predictions = pd.DataFrame({"row": test_idx, "actual": target[test_idx]})
    models = {
        "LDA": make_pipeline(StandardScaler(), LinearDiscriminantAnalysis()),
        "QDA": make_pipeline(StandardScaler(), QuadraticDiscriminantAnalysis(reg_param=0.05)),
    }
    for name, model in models.items():
        model.fit(data.iloc[train_idx][FEATURES], target[train_idx])
        predicted = model.predict(data.iloc[test_idx][FEATURES])
        predictions[name] = predicted
        matrix = confusion_matrix(target[test_idx], predicted, labels=[0, 1, 2])
        outputs[name] = {
            "accuracy": float(accuracy_score(target[test_idx], predicted)),
            "balanced_accuracy": float(balanced_accuracy_score(target[test_idx], predicted)),
            "confusion_matrix_labels_0_1_2": matrix.tolist(),
        }
    predictions.to_csv(args.output_dir / f"{LAB_ID}_predictions.csv", index=False)
    result = {
        "lab_id": LAB_ID,
        "seed": SEED,
        "split": {"test_size": 0.25, "stratified": True, "random_state": SEED},
        "preprocessing": "StandardScaler is inside each Pipeline and is fitted on training rows only",
        "models": outputs,
        "checks": {
            "train_rows": int(len(train_idx)),
            "test_rows": int(len(test_idx)),
            "no_row_overlap": bool(set(train_idx).isdisjoint(set(test_idx))),
            "all_test_predictions_finite": bool(np.isfinite(predictions[["LDA", "QDA"]].to_numpy()).all()),
        },
    }
    (args.output_dir / f"{LAB_ID}_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
