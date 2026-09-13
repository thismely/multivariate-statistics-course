#!/usr/bin/env python3
"""Offline multiple linear-regression laboratory with train-only scaling."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

SEED = 6501
LAB_ID = "regression"
FEATURES = ["predictor_1", "predictor_2", "predictor_3", "predictor_4", "predictor_5"]


def make_data() -> tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(SEED)
    x = rng.normal(size=(210, len(FEATURES)))
    x[:, 1] = 0.45 * x[:, 0] + np.sqrt(1 - 0.45**2) * x[:, 1]
    y = 2.8 * x[:, 0] - 2.1 * x[:, 1] + 1.25 * x[:, 2] + 0.4 * x[:, 3] + rng.normal(scale=0.65, size=len(x))
    return pd.DataFrame(x, columns=FEATURES), y


def metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "r2": float(r2_score(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "mae": float(mean_absolute_error(actual, predicted)),
    }


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
    train_idx, test_idx = train_test_split(np.arange(len(target)), test_size=0.25, random_state=SEED)
    scaler = StandardScaler().fit(data.iloc[train_idx][FEATURES])
    x_train = scaler.transform(data.iloc[train_idx][FEATURES])
    x_test = scaler.transform(data.iloc[test_idx][FEATURES])
    model = LinearRegression().fit(x_train, target[train_idx])
    train_pred = model.predict(x_train)
    test_pred = model.predict(x_test)
    data.assign(target=target).to_csv(args.output_dir / f"{LAB_ID}_data.csv", index=False)
    pd.DataFrame({"actual": target[test_idx], "predicted": test_pred}).to_csv(
        args.output_dir / f"{LAB_ID}_predictions.csv", index=False
    )
    result = {
        "lab_id": LAB_ID,
        "seed": SEED,
        "split": {"test_size": 0.25, "random_state": SEED},
        "preprocessing": "StandardScaler fitted on training rows only; coefficients are per standardised predictor",
        "standardized_coefficients": {name: float(value) for name, value in zip(FEATURES, model.coef_)},
        "intercept": float(model.intercept_),
        "train_metrics": metrics(target[train_idx], train_pred),
        "test_metrics": metrics(target[test_idx], test_pred),
        "checks": {
            "train_rows": int(len(train_idx)),
            "test_rows": int(len(test_idx)),
            "no_row_overlap": bool(set(train_idx).isdisjoint(set(test_idx))),
            "predictions_finite": bool(np.isfinite(test_pred).all()),
        },
    }
    (args.output_dir / f"{LAB_ID}_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
