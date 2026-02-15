#!/usr/bin/env python
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path


def analyze(csv_path: str):
    p = Path(csv_path)
    if not p.exists():
        print(f"File not found: {csv_path}")
        return 2

    df = pd.read_csv(p, parse_dates=["date"])
    if df.empty:
        print("CSV is empty")
        return 2

    # ensure columns
    if not {"date", "return", "regime"}.issubset(df.columns):
        print("CSV missing required columns (date, return, regime)")
        return 2

    df = df.sort_values("date").reset_index(drop=True)
    df["regime"] = df["regime"].astype(int)

    n = len(df)
    regimes = sorted(df["regime"].unique())
    stats = {
        "n_observations": int(n),
        "n_regimes": int(len(regimes)),
    }

    # time in regime
    counts = df["regime"].value_counts().to_dict()
    pct = {int(k): float(v) / n for k, v in counts.items()}

    # returns by regime
    agg = df.groupby("regime")["return"].agg(["mean", "median", "std"]).to_dict()

    # run-lengths (consecutive same-regime periods)
    runs = {}
    prev = None
    length = 0
    for r in df["regime"]:
        if r == prev:
            length += 1
        else:
            if prev is not None:
                runs.setdefault(prev, []).append(length)
            prev = r
            length = 1
    if prev is not None:
        runs.setdefault(prev, []).append(length)

    run_stats = {int(k): {"count": len(v), "mean_length": float(np.mean(v)), "median_length": float(np.median(v))} for k, v in runs.items()}

    # transition matrix
    max_r = max(regimes)
    size = max_r + 1
    trans = np.zeros((size, size), dtype=int)
    prev = df["regime"].iloc[0]
    for cur in df["regime"].iloc[1:]:
        trans[prev, cur] += 1
        prev = cur
    trans_prob = trans.astype(float)
    row_sums = trans_prob.sum(axis=1)
    for i in range(size):
        if row_sums[i] > 0:
            trans_prob[i, :] /= row_sums[i]

    # prepare report
    report = {
        "summary": stats,
        "counts": {int(k): int(v) for k, v in counts.items()},
        "pct": {int(k): v for k, v in pct.items()},
        "returns": {int(k): {"mean": float(agg["mean"][k]), "median": float(agg["median"][k]), "std": float(agg["std"][k])} for k in agg["mean"]},
        "run_stats": run_stats,
        "transition_counts": trans.tolist(),
        "transition_probabilities": trans_prob.tolist(),
    }

    out_txt = p.with_name(p.stem + "_report.txt")
    with open(out_txt, "w") as f:
        f.write("Markov regimes analysis\n")
        f.write(json.dumps(report, indent=2))

    out_json = p.with_name(p.stem + "_report.json")
    with open(out_json, "w") as f:
        json.dump(report, f, indent=2)

    # also print a concise summary
    print(f"File: {p}\nObservations: {n} regimes: {regimes}")
    print("Counts:", counts)
    print("Pct:", {k: f"{v:.2%}" for k, v in pct.items()})
    print("Run stats:", run_stats)
    print("Transition probabilities matrix:")
    print(pd.DataFrame(trans_prob).fillna(0))
    print(f"Reports written: {out_txt}, {out_json}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: markov_analysis.py <csv_path>")
        sys.exit(2)
    sys.exit(analyze(sys.argv[1]))
