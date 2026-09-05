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
    st_series = get_supertrend(high, low, close, lookback, multiplier)
    st_series = pd.Series(st_series).reindex(close.index)

    prev_close = close.shift(1)
    prev_st = st_series.shift(1)

    sig = pd.Series(0, index=close.index, dtype=int)
    buy_mask = prev_close.notna() & prev_st.notna() & (prev_close <= prev_st) & (close > st_series)
    sell_mask = prev_close.notna() & prev_st.notna() & (prev_close >= prev_st) & (close < st_series)
    sig[buy_mask] = 1
    sig[sell_mask] = -1
    return st_series, sig


def macd_signal(close: pd.Series, fast: int = 12, slow: int = 26, signal_span: int = 9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_span, adjust=False).mean()
    prev_macd = macd_line.shift(1)
    prev_signal = signal_line.shift(1)

    sig = pd.Series(0, index=close.index, dtype=int)
    sig[(prev_macd <= prev_signal) & (macd_line > signal_line)] = 1
    sig[(prev_macd >= prev_signal) & (macd_line < signal_line)] = -1
    return macd_line, signal_line, sig


def ema_cross_signal(close: pd.Series, fast: int = 20, slow: int = 50):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    prev_fast = ema_fast.shift(1)
    prev_slow = ema_slow.shift(1)

    sig = pd.Series(0, index=close.index, dtype=int)
    sig[(prev_fast <= prev_slow) & (ema_fast > ema_slow)] = 1
    sig[(prev_fast >= prev_slow) & (ema_fast < ema_slow)] = -1
    return ema_fast, ema_slow, sig


def ema_trend_signal(close: pd.Series, fast_period: int = 20, slow_period: int = 50, momentum_period: int = 10):
    ema_fast = close.ewm(span=fast_period, adjust=False).mean()
    ema_slow = close.ewm(span=slow_period, adjust=False).mean()
    momentum = close.pct_change(periods=momentum_period)
    prev_fast = ema_fast.shift(1)
    prev_slow = ema_slow.shift(1)
    prev_momentum = momentum.shift(1)

    sig = pd.Series(0, index=close.index, dtype=int)
    buy_mask = (prev_fast <= prev_slow) & (ema_fast > ema_slow) & (close > ema_fast) & (prev_momentum <= 0) & (momentum > 0)
    sell_mask = (prev_fast >= prev_slow) & (ema_fast < ema_slow) & (close < ema_fast) & (prev_momentum >= 0) & (momentum < 0)
    sig[buy_mask] = 1
    sig[sell_mask] = -1
    return ema_fast, ema_slow, momentum, sig


def bollinger_signal(close: pd.Series, window: int = 20, num_std: int = 2):
    mid = close.rolling(window=window, min_periods=window).mean()
    std = close.rolling(window=window, min_periods=window).std(ddof=0)
    upper = mid + (num_std * std)
    lower = mid - (num_std * std)

    prev_close = close.shift(1)
    prev_lower = lower.shift(1)
    prev_upper = upper.shift(1)
    sig = pd.Series(0, index=close.index, dtype=int)
    sig[(prev_close >= prev_lower) & (close < lower)] = 1
    sig[(prev_close <= prev_upper) & (close > upper)] = -1
    return upper, mid, lower, sig


def stochastic_signal(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3):
    lowest_low = low.rolling(window=k_period, min_periods=k_period).min()
    highest_high = high.rolling(window=k_period, min_periods=k_period).max()
    denominator = (highest_high - lowest_low).replace(0, np.nan)
    k = ((close - lowest_low) / denominator) * 100
    d = k.rolling(window=d_period, min_periods=d_period).mean()
    prev_k = k.shift(1)
    prev_d = d.shift(1)

    sig = pd.Series(0, index=close.index, dtype=int)
    sig[(prev_k <= prev_d) & (k > d) & (k < 20)] = 1
    sig[(prev_k >= prev_d) & (k < d) & (k > 80)] = -1
    return k, d, sig


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
