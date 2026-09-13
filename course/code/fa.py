#!/usr/bin/env python3
"""Offline exploratory factor-analysis laboratory with fixed-seed data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import FactorAnalysis
from sklearn.preprocessing import StandardScaler

SEED = 6201
LAB_ID = "fa"
FEATURES = ["survey_item_1", "survey_item_2", "survey_item_3", "survey_item_4", "survey_item_5", "survey_item_6"]


def make_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    factors = rng.normal(size=(220, 2))
    loading = np.array(
        [[0.82, 0.08], [0.76, 0.20], [0.70, -0.12], [0.12, 0.86], [0.26, 0.78], [-0.16, 0.72]]
    )
    observed = factors @ loading.T + rng.normal(scale=0.35, size=(220, len(FEATURES)))
    return pd.DataFrame(observed, columns=FEATURES)


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
    scaled = StandardScaler().fit_transform(data[FEATURES])
    model = FactorAnalysis(n_components=2, rotation="varimax", random_state=SEED)
    scores = model.fit_transform(scaled)
    loadings = model.components_.T
    communalities = np.sum(loadings**2, axis=1)

    data.to_csv(args.output_dir / f"{LAB_ID}_data.csv", index=False)
    pd.DataFrame(scores, columns=["factor_1", "factor_2"]).to_csv(
        args.output_dir / f"{LAB_ID}_scores.csv", index=False
    )
    result = {
        "lab_id": LAB_ID,
        "seed": SEED,
        "n_samples": int(data.shape[0]),
        "n_features": int(data.shape[1]),
        "preprocessing": "StandardScaler fitted on the synthetic observation matrix",
        "model": "sklearn FactorAnalysis(n_components=2, rotation='varimax')",
        "pca_difference": "FA models common and unique variance; PCA seeks directions of total variance",
        "loadings": {
            name: [float(v) for v in row] for name, row in zip(FEATURES, loadings)
        },
        "communalities": {name: float(v) for name, v in zip(FEATURES, communalities)},
        "uniqueness": {name: float(v) for name, v in zip(FEATURES, model.noise_variance_)},
        "checks": {
            "communalities_in_unit_interval": bool(np.all((communalities >= 0) & (communalities <= 1.0 + 1e-6))),
            "scores_finite": bool(np.isfinite(scores).all()),
        },
    }
    (args.output_dir / f"{LAB_ID}_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
