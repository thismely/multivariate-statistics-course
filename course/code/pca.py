#!/usr/bin/env python3
"""Offline PCA laboratory with deterministic synthetic observations.

The data are generated in this file with a fixed seed.  No course, student,
or personally identifiable data are read.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

SEED = 6101
LAB_ID = "pca"
FEATURES = ["indicator_1", "indicator_2", "indicator_3", "indicator_4", "indicator_5"]


def make_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    latent = rng.normal(size=(180, 2))
    loading = np.array(
        [[0.88, 0.12], [0.76, 0.22], [0.18, 0.90], [-0.18, 0.82], [0.60, -0.30]]
    )
    noise = rng.normal(scale=0.20, size=(180, len(FEATURES)))
    x = latent @ loading.T + noise
    # Deliberately different measurement units make standardisation observable.
    x = x * np.array([20.0, 10.0, 5.0, 2.0, 50.0]) + np.array([100, 40, 8, 2, 300])
    return pd.DataFrame(x, columns=FEATURES)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
        help="directory for generated CSV and JSON results",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    data = make_data()
    scaled = StandardScaler().fit_transform(data[FEATURES])
    model = PCA(n_components=2).fit(scaled)
    scores = model.transform(scaled)
    loadings = model.components_.T * np.sqrt(model.explained_variance_)

    data.to_csv(args.output_dir / f"{LAB_ID}_data.csv", index=False)
    pd.DataFrame(scores, columns=["PC1", "PC2"]).to_csv(
        args.output_dir / f"{LAB_ID}_scores.csv", index=False
    )
    explained = model.explained_variance_ratio_.tolist()
    result = {
        "lab_id": LAB_ID,
        "seed": SEED,
        "n_samples": int(data.shape[0]),
        "n_features": int(data.shape[1]),
        "preprocessing": "StandardScaler fitted on the synthetic observation matrix before PCA",
        "components": 2,
        "explained_variance_ratio": [float(v) for v in explained],
        "cumulative_variance_ratio": [float(v) for v in np.cumsum(explained)],
        "loadings": {
            name: [float(v) for v in row] for name, row in zip(FEATURES, loadings)
        },
        "checks": {
            "variance_ratio_positive": bool(np.all(model.explained_variance_ratio_ > 0)),
            "components_orthogonal": bool(
                np.isclose(np.dot(model.components_[0], model.components_[1]), 0.0, atol=1e-10)
            ),
        },
    }
    (args.output_dir / f"{LAB_ID}_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
