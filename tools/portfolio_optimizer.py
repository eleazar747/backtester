#!/usr/bin/env python
"""Portfolio optimizer: select top-N tickers by data availability and
compute weights that maximize Sharpe ratio (no shorting) using mean-variance.

Outputs weights and portfolio metrics to CSV.
"""
import argparse
import os
from typing import List

import numpy as np
import pandas as pd
from pathlib import Path

import django
from pathlib import Path as _Path
import sys as _sys

# Ensure project root is on sys.path so Django can import settings when run as script
_ROOT = _Path(__file__).resolve().parents[1]
_sys.path.insert(0, str(_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stockmarket.settings")
django.setup()

from historical_price.models import historical_price
from referential.models import securitydescription
from django.db.models import Q, Count


def choose_top_n_tickers(n: int, country: str = None, market: str = None, min_history: int = None) -> List[str]:
    # Optionally filter tickers by country using referential.securitydescription
    if country:
        # map common country inputs to expected stored values for US
        country = country.strip()
        if country.upper() in ("US", "USA", "U.S.", "U.S.A."):
            candidates = securitydescription.objects.filter(
                country__in=["United States", "United States of America", "USA", "US"]
            ).values_list("yahoo_id", flat=True)
        else:
            candidates = securitydescription.objects.filter(country__icontains=country).values_list("yahoo_id", flat=True)
        vals = list(historical_price.objects.filter(yahoo_id__in=list(candidates)).values_list("yahoo_id", flat=True))
    elif market:
        # market may be comma-separated values like 'nasdaq,nyse' or special token 'us_market'
        tokens = [m.strip() for m in market.split(",") if m.strip()]
        # build exact, case-insensitive filter on securitydescription.market_place
        q = Q()
        for tok in tokens:
            q |= Q(market_place__iexact=tok)

        # first filter securitydescription to get candidate yahoo_ids
        candidate_ids = list(securitydescription.objects.filter(q).values_list("yahoo_id", flat=True))
        if not candidate_ids:
            return []

        # now count available historical_price rows for those candidates and pick top N
        counts_qs = (
            historical_price.objects.filter(yahoo_id__in=candidate_ids)
            .values("yahoo_id")
            .annotate(cnt=Count("id"))
            .order_by("-cnt")
        )
        top = [row["yahoo_id"] for row in counts_qs[:n]]
        return top
    else:
        vals = list(historical_price.objects.values_list("yahoo_id", flat=True))

    if not vals:
        return []
    ser = pd.Series(vals).value_counts()
    if min_history:
        ser = ser[ser >= min_history]
    return ser.index.astype(str).tolist()[:n]


def load_prices(tickers: List[str]) -> pd.DataFrame:
    # load close prices for each ticker and align by date (inner join)
    frames = []
    for t in tickers:
        qs = historical_price.objects.filter(yahoo_id=t).order_by("spot_date").values("spot_date", "close_price")
        df = pd.DataFrame(list(qs))
        if df.empty:
            continue
        df["spot_date"] = pd.to_datetime(df["spot_date"]).dt.date
        # if there are duplicate dates, take last available price for that date
        df = df.groupby("spot_date")["close_price"].last().rename(t).astype(float)
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    prices = pd.concat(frames, axis=1, join="inner").sort_index()
    return prices


def annualize_return_and_cov(returns: pd.DataFrame, trading_days: int = 252):
    mu = returns.mean() * trading_days
    cov = returns.cov() * trading_days
    return mu.values, cov.values


def max_sharpe_weights(mu: np.ndarray, cov: np.ndarray, rf: float = 0.0):
    # maximize (w^T mu - rf) / sqrt(w^T cov w)  == minimize negative Sharpe
    n = len(mu)
    x0 = np.ones(n) / n

    def neg_sharpe(w):
        w = np.array(w)
        port_ret = np.dot(w, mu)
        port_var = float(w.T.dot(cov).dot(w))
        if port_var <= 0:
            return 1e6
        sharpe = (port_ret - rf) / np.sqrt(port_var)
        return -sharpe

    cons = ({"type": "eq", "fun": lambda w: np.sum(w) - 1.0},)
    bounds = [(0.0, 1.0) for _ in range(n)]

    from scipy.optimize import minimize

    res = minimize(neg_sharpe, x0, method="SLSQP", bounds=bounds, constraints=cons)
    if not res.success:
        # fallback equal weights
        return x0
    return res.x


def main(n: int, out_path: str):
    tickers = choose_top_n_tickers(n)
    if not tickers:
        print("No tickers found in historical_price table.")
        return 1
    tickers = tickers[:n]
    print(f"Selected {len(tickers)} tickers")

    prices = load_prices(tickers)
    if prices.empty:
        print("No aligned price data for selected tickers (empty after intersection).")
        return 1

    # daily returns
    returns = prices.pct_change().dropna()
    mu, cov = annualize_return_and_cov(returns)

    # regularize covariance in case it's singular
    cov += np.eye(cov.shape[0]) * 1e-8

    weights = max_sharpe_weights(mu, cov, rf=0.0)

    port_ret = float(weights.dot(mu))
    port_vol = float(np.sqrt(weights.T.dot(cov).dot(weights)))
    sharpe = (port_ret) / port_vol if port_vol > 0 else 0.0

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    df_out = pd.DataFrame({"ticker": tickers, "weight": weights})
    df_out["expected_annual_return"] = df_out["ticker"].map({t: float(mu[i]) for i, t in enumerate(tickers)})
    df_out["expected_annual_vol"] = df_out["ticker"].map({t: float(np.sqrt(cov[i, i])) for i, t in enumerate(tickers)})
    df_out.to_csv(out, index=False)

    summary = {"n_tickers": len(tickers), "portfolio_return": port_ret, "portfolio_vol": port_vol, "sharpe": sharpe}
    summary_path = out.with_name(out.stem + "_summary.json")
    import json

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved weights to {out}")
    print(f"Saved summary to {summary_path}")
    print(summary)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=20, help="number of tickers to select")
    parser.add_argument("--out", default="results/portfolio_20.csv", help="output CSV path")
    parser.add_argument("--country", default=None, help="optional country filter (e.g. US)")
    parser.add_argument("--market", default=None, help="optional market filter (comma-separated, e.g. nasdaq,nyse)")
    parser.add_argument("--min_history", type=int, default=None, help="minimum historical rows required per ticker")
    args = parser.parse_args()
    main(args.n, args.out)
