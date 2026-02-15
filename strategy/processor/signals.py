import pandas as pd
import numpy as np
from datetime import datetime
from referential.models import securitydescription
from historical_price.models import historical_price
from .supertrendstrat import get_supertrend


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def rsi_signal(rsi_series: pd.Series) -> pd.Series:
    # 1 if RSI < 30, -1 if RSI > 70, 0 otherwise
    sig = pd.Series(index=rsi_series.index, dtype=int)
    sig[rsi_series < 30] = 1
    sig[rsi_series > 70] = -1
    mask = (rsi_series >= 30) & (rsi_series <= 70)
    sig[mask] = 0
    return sig.fillna(0).astype(int)


def supertrend_signal(high: pd.Series, low: pd.Series, close: pd.Series, lookback: int = 10, multiplier: int = 3):
    # reuse get_supertrend which returns st list aligned with prices
    try:
        _, _, _, st_list, _ = get_supertrend(high, low, close, lookback, multiplier, 'tmp', None, close.index)
    except Exception:
        # fallback: create NaN series
        st_list = [np.nan] * len(close)

    st_series = pd.Series(st_list, index=close.index)
    # 1 if close > st, -1 if close < st
    sig = pd.Series(index=close.index, dtype=int)
    sig[close > st_series] = 1
    sig[close < st_series] = -1
    sig[close == st_series] = 0
    return st_series, sig.fillna(0).astype(int)


def generate_signals_for_all(last_n: int = 252, rsi_period: int = 14, st_lookback: int = 10, st_multiplier: int = 3, out_csv: str = None):
    symbols = securitydescription.objects.all().values_list('yahoo_id', flat=True)
    results = []

    for yahoo_id in symbols:
        histo_qs = (
            historical_price.objects.filter(yahoo_id=yahoo_id)
            .order_by('-spot_date')
            .values('spot_date', 'high_price', 'low_price', 'close_price')
        )
        df = pd.DataFrame(list(histo_qs))
        if df.empty or len(df) < 20:
            continue
        df = df.set_index('spot_date').sort_index()
        df = df.iloc[-last_n:]

        close = df['close_price']
        high = df['high_price']
        low = df['low_price']

        rsi = compute_rsi(close, period=rsi_period)
        rsi_sig = rsi_signal(rsi)

        st_series, st_sig = supertrend_signal(high, low, close, lookback=st_lookback, multiplier=st_multiplier)

        out = pd.DataFrame({
            'yahoo_id': yahoo_id,
            'close': close,
            'rsi': rsi,
            'rsi_signal': rsi_sig,
            'supertrend': st_series,
            'st_signal': st_sig,
        })
        out.index.name = 'spot_date'
        results.append(out.reset_index())

    if not results:
        return {}

    all_df = pd.concat(results, ignore_index=True)
    if out_csv:
        all_df.to_csv(out_csv, index=False)

    # return dictionary grouped by ticker for convenience
    grouped = {k: g.drop(columns=['yahoo_id']).set_index('spot_date') for k, g in all_df.groupby('yahoo_id')}
    return grouped


if __name__ == '__main__':
    # quick runner: write CSV to results/signals.csv
    generate_signals_for_all(out_csv='results/signals.csv')
