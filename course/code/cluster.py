#!/usr/bin/env python3
"""Offline K-means and Ward clustering laboratory with synthetic data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.datasets import make_blobs
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

SEED = 6301
LAB_ID = "cluster"
FEATURES = ["feature_1", "feature_2", "feature_3", "feature_4"]


def make_data() -> tuple[pd.DataFrame, np.ndarray]:
    x, truth = make_blobs(
        n_samples=180,
        centers=np.array([[-2.8, -1.7, 0.0, 0.8], [0.0, 2.5, 2.0, -1.8], [3.0, -0.4, -2.3, 1.8]]),
        cluster_std=0.72,
        random_state=SEED,
    )
    return pd.DataFrame(x, columns=FEATURES), truth


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    data, truth = make_data()
    scaled = StandardScaler().fit_transform(data[FEATURES])
    kmeans = KMeans(n_clusters=3, n_init=20, random_state=SEED)
    kmeans_labels = kmeans.fit_predict(scaled)
    ward_labels = AgglomerativeClustering(n_clusters=3, linkage="ward").fit_predict(scaled)
    data = data.assign(synthetic_group=truth, kmeans_cluster=kmeans_labels, ward_cluster=ward_labels)
    data.to_csv(args.output_dir / f"{LAB_ID}_data.csv", index=False)

    def counts(labels: np.ndarray) -> dict[str, int]:
        return {str(int(label)): int(np.sum(labels == label)) for label in sorted(np.unique(labels))}

    result = {
        "lab_id": LAB_ID,
        "seed": SEED,
        "n_samples": int(len(data)),
        "preprocessing": "StandardScaler fitted before distance-based clustering",
        "kmeans": {
            "n_clusters": 3,
            "inertia": float(kmeans.inertia_),
            "silhouette": float(silhouette_score(scaled, kmeans_labels)),
            "cluster_counts": counts(kmeans_labels),
            "adjusted_rand_against_synthetic_truth": float(adjusted_rand_score(truth, kmeans_labels)),
        },
        "ward": {
            "silhouette": float(silhouette_score(scaled, ward_labels)),
            "cluster_counts": counts(ward_labels),
            "adjusted_rand_against_synthetic_truth": float(adjusted_rand_score(truth, ward_labels)),
        },
        "checks": {
            "three_nonempty_kmeans_clusters": bool(len(np.unique(kmeans_labels)) == 3),
            "silhouette_in_valid_range": bool(-1.0 <= silhouette_score(scaled, kmeans_labels) <= 1.0),
        },
    }
    (args.output_dir / f"{LAB_ID}_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
