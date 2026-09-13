#!/usr/bin/env python3
"""Offline entropy-weighted TOPSIS comprehensive-evaluation laboratory."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 6901
LAB_ID = "evaluation"
INDICATORS = ["income", "employment", "innovation", "pollution", "debt", "service"]
DIRECTIONS = {"income": "benefit", "employment": "benefit", "innovation": "benefit", "pollution": "cost", "debt": "cost", "service": "benefit"}


def make_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    values = np.column_stack(
        [
            rng.normal(65, 8, 12),
            rng.normal(72, 7, 12),
            rng.normal(55, 10, 12),
            rng.normal(38, 6, 12),
            rng.normal(48, 9, 12),
            rng.normal(60, 8, 12),
        ]
    )
    return pd.DataFrame(values, index=[f"region_{i:02d}" for i in range(1, 13)], columns=INDICATORS)


def minmax_oriented(data: pd.DataFrame) -> pd.DataFrame:
    normalized = pd.DataFrame(index=data.index, columns=data.columns, dtype=float)
    for name in data.columns:
        low, high = float(data[name].min()), float(data[name].max())
        span = high - low
        if span == 0:
            normalized[name] = 1.0
        elif DIRECTIONS[name] == "benefit":
            normalized[name] = (data[name] - low) / span
        else:
            normalized[name] = (high - data[name]) / span
    return normalized.clip(lower=0.0, upper=1.0)


def entropy_weights(normalized: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    eps = np.finfo(float).eps
    proportions = normalized.div(normalized.sum(axis=0).replace(0, eps), axis=1).clip(lower=eps)
    k = 1.0 / np.log(len(normalized))
    entropy = -k * (proportions * np.log(proportions)).sum(axis=0)
    divergence = (1.0 - entropy).clip(lower=eps)
    return divergence / divergence.sum(), entropy


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
    data.to_csv(args.output_dir / f"{LAB_ID}_data.csv", index_label="unit")
    normalized = minmax_oriented(data)
    weights, entropy = entropy_weights(normalized)
    weighted = normalized * weights
    ideal_best = weighted.max(axis=0)
    ideal_worst = weighted.min(axis=0)
    distance_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    distance_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))
    scores = distance_worst / (distance_best + distance_worst).replace(0, np.finfo(float).eps)
    ranking = scores.rank(method="min", ascending=False).astype(int)
    output = data.copy()
    output["topsis_score"] = scores
    output["rank"] = ranking
    output.to_csv(args.output_dir / f"{LAB_ID}_scores.csv", index_label="unit")
    normalized.to_csv(args.output_dir / f"{LAB_ID}_normalized.csv", index_label="unit")
    result = {
        "lab_id": LAB_ID,
        "seed": SEED,
        "n_units": int(len(data)),
        "directions": DIRECTIONS,
        "preprocessing": "Min-max normalization oriented by benefit/cost direction; no student or administrative data",
        "weighting": "Entropy weights computed from normalized indicators",
        "entropy": {name: float(v) for name, v in entropy.items()},
        "weights": {name: float(v) for name, v in weights.items()},
        "ranked_units": [
            {"unit": str(index), "score": float(scores[index]), "rank": int(ranking[index])}
            for index in scores.sort_values(ascending=False).index
        ],
        "checks": {
            "weight_sum_one": bool(np.isclose(weights.sum(), 1.0)),
            "scores_in_unit_interval": bool(np.all((scores >= 0) & (scores <= 1))),
            "all_ranks_present": bool(set(ranking) == set(range(1, len(data) + 1))),
        },
    }
    (args.output_dir / f"{LAB_ID}_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
