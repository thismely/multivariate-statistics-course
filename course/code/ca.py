#!/usr/bin/env python3
"""Offline correspondence analysis laboratory implemented with SVD."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 6801
LAB_ID = "ca"
ROW_LABELS = ["region_1", "region_2", "region_3", "region_4", "region_5", "region_6"]
COL_LABELS = ["profile_A", "profile_B", "profile_C", "profile_D", "profile_E"]


def make_table() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rate = np.array(
        [[42, 22, 8, 5, 3], [35, 28, 9, 4, 3], [8, 12, 38, 20, 8], [6, 10, 32, 25, 12], [5, 6, 12, 36, 28], [3, 7, 10, 28, 40]],
        dtype=float,
    )
    table = rng.poisson(rate)
    table[table < 1] = 1
    return pd.DataFrame(table, index=ROW_LABELS, columns=COL_LABELS)


def correspondence_analysis(table: np.ndarray, dimensions: int = 2) -> dict[str, np.ndarray]:
    total = table.sum()
    p = table / total
    row_mass = p.sum(axis=1)
    col_mass = p.sum(axis=0)
    expected = np.outer(row_mass, col_mass)
    standardized = (p - expected) / np.sqrt(np.outer(row_mass, col_mass))
    # The singular-value decomposition is the core CA eigensystem.
    u, singular_values, vt = np.linalg.svd(standardized, full_matrices=False)
    row_coordinates = u[:, :dimensions] * singular_values[:dimensions] / np.sqrt(row_mass[:, None])
    col_coordinates = vt.T[:, :dimensions] * singular_values[:dimensions] / np.sqrt(col_mass[:, None])
    inertia = singular_values**2
    return {
        "row_mass": row_mass,
        "col_mass": col_mass,
        "singular_values": singular_values,
        "inertia": inertia,
        "row_coordinates": row_coordinates,
        "col_coordinates": col_coordinates,
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

    table = make_table()
    ca = correspondence_analysis(table.to_numpy(dtype=float))
    table.to_csv(args.output_dir / f"{LAB_ID}_table.csv", index_label="row_category")
    pd.DataFrame(ca["row_coordinates"], index=ROW_LABELS, columns=["dim_1", "dim_2"]).to_csv(
        args.output_dir / f"{LAB_ID}_row_coordinates.csv", index_label="row_category"
    )
    pd.DataFrame(ca["col_coordinates"], index=COL_LABELS, columns=["dim_1", "dim_2"]).to_csv(
        args.output_dir / f"{LAB_ID}_column_coordinates.csv", index_label="column_category"
    )
    inertia_ratio = ca["inertia"] / ca["inertia"].sum()
    result = {
        "lab_id": LAB_ID,
        "seed": SEED,
        "table_shape": list(table.shape),
        "preprocessing": "Row and column profiles are centered by independence expectation and mass-weighted",
        "decomposition": "SVD of the standardized residual matrix",
        "singular_values": [float(v) for v in ca["singular_values"][:2]],
        "inertia_ratio_first_two": [float(v) for v in inertia_ratio[:2]],
        "row_masses": {name: float(v) for name, v in zip(ROW_LABELS, ca["row_mass"])},
        "column_masses": {name: float(v) for name, v in zip(COL_LABELS, ca["col_mass"])},
        "checks": {
            "row_masses_sum_to_one": bool(np.isclose(ca["row_mass"].sum(), 1.0)),
            "column_masses_sum_to_one": bool(np.isclose(ca["col_mass"].sum(), 1.0)),
            "inertia_ratio_sum_to_one": bool(np.isclose(inertia_ratio.sum(), 1.0)),
        },
    }
    (args.output_dir / f"{LAB_ID}_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
