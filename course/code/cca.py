#!/usr/bin/env python3
"""Offline canonical-correlation analysis with train-fitted block scaling."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cross_decomposition import CCA
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

SEED = 6701
LAB_ID = "cca"
X_FEATURES = ["input_1", "input_2", "input_3", "input_4"]
Y_FEATURES = ["outcome_1", "outcome_2", "outcome_3"]


def make_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    latent = rng.normal(size=(240, 2))
    x_loading = np.array([[0.9, 0.1], [0.7, 0.3], [0.2, 0.8], [-0.1, 0.7]])
    y_loading = np.array([[0.8, 0.2], [0.5, 0.6], [0.1, 0.9]])
    x = latent @ x_loading.T + rng.normal(scale=0.35, size=(240, len(X_FEATURES)))
    y = latent @ y_loading.T + rng.normal(scale=0.35, size=(240, len(Y_FEATURES)))
    return pd.DataFrame(np.column_stack([x, y]), columns=X_FEATURES + Y_FEATURES)


def pair_correlations(x_scores: np.ndarray, y_scores: np.ndarray) -> list[float]:
    return [float(abs(np.corrcoef(x_scores[:, i], y_scores[:, i])[0, 1])) for i in range(x_scores.shape[1])]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    data = make_data()
    train_idx, test_idx = train_test_split(np.arange(len(data)), test_size=0.25, random_state=SEED)
    x_scaler = StandardScaler().fit(data.iloc[train_idx][X_FEATURES])
    y_scaler = StandardScaler().fit(data.iloc[train_idx][Y_FEATURES])
    x_train = x_scaler.transform(data.iloc[train_idx][X_FEATURES])
    x_test = x_scaler.transform(data.iloc[test_idx][X_FEATURES])
    y_train = y_scaler.transform(data.iloc[train_idx][Y_FEATURES])
    y_test = y_scaler.transform(data.iloc[test_idx][Y_FEATURES])
    model = CCA(n_components=2, scale=False, max_iter=2000, tol=1e-7)
    model.fit(x_train, y_train)
    x_train_c, y_train_c = model.transform(x_train, y_train)
    x_test_c, y_test_c = model.transform(x_test, y_test)
    train_corr = pair_correlations(x_train_c, y_train_c)
    test_corr = pair_correlations(x_test_c, y_test_c)

    data.to_csv(args.output_dir / f"{LAB_ID}_data.csv", index=False)
    pd.DataFrame(
        {"canonical_pair": [1, 2], "train_abs_correlation": train_corr, "test_abs_correlation": test_corr}
    ).to_csv(args.output_dir / f"{LAB_ID}_correlations.csv", index=False)
    result = {
        "lab_id": LAB_ID,
        "seed": SEED,
        "split": {"test_size": 0.25, "random_state": SEED},
        "block_dimensions": {"X": len(X_FEATURES), "Y": len(Y_FEATURES)},
        "preprocessing": "Separate X and Y StandardScaler objects fitted on training rows only; CCA scale=False",
        "train_absolute_canonical_correlations": train_corr,
        "test_absolute_canonical_correlations": test_corr,
        "checks": {
            "components": 2,
            "no_row_overlap": bool(set(train_idx).isdisjoint(set(test_idx))),
            "test_correlations_in_unit_interval": bool(np.all((np.array(test_corr) >= 0) & (np.array(test_corr) <= 1))),
        },
    }
    (args.output_dir / f"{LAB_ID}_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
