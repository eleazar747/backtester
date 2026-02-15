import logging
from typing import Optional, Dict, Any

import pandas as pd
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

from historical_price.models import historical_price

logger = logging.getLogger(__name__)


def load_close_series(yahoo_id: str, start: Optional[str] = None, end: Optional[str] = None) -> pd.Series:
    """Load `close_price` time series from `historical_price` for a ticker.

    Returns a pandas Series indexed by `spot_date` (sorted ascending). If no
    data is found an empty Series is returned.
    """
    qs = (
        historical_price.objects.filter(yahoo_id=yahoo_id)
        .order_by("spot_date")
        .values("spot_date", "close_price")
    )
    df = pd.DataFrame(list(qs))
    if df.empty:
        return pd.Series(dtype="float64")
    df["spot_date"] = pd.to_datetime(df["spot_date"])
    df.set_index("spot_date", inplace=True)
    s = df["close_price"].astype("float64")
    if start:
        s = s[s.index >= pd.to_datetime(start)]
    if end:
        s = s[s.index <= pd.to_datetime(end)]
    return s


def fit_markov_switch(
    yahoo_id: str,
    k_regimes: int = 2,
    trend: str = "c",
    switching_variance: bool = True,
    start: Optional[str] = None,
    end: Optional[str] = None,
    **fit_kwargs: Any,
) -> Optional[Dict[str, Any]]:
    """Fit a Markov switching model on log-returns of `close_price`.

    Returns a dict with `model`, `result`, `regimes`, `returns` and `dates`.
    If no data is available for the ticker the function returns `None`.
    """
    s = load_close_series(yahoo_id, start=start, end=end)
    if s.empty:
        logger.warning("No historical close prices found for %s", yahoo_id)
        return None

    # compute simple returns and drop NaNs
    returns = s.pct_change().dropna()
    if returns.empty:
        logger.warning("Not enough data after differencing for %s", yahoo_id)
        return None

    # statsmodels expects an array-like endog
    try:
        model = MarkovRegression(returns.values, k_regimes=k_regimes, trend=trend, switching_variance=switching_variance)
        result = model.fit(**fit_kwargs)
        regimes = result.predict()
        return {"model": model, "result": result, "regimes": regimes, "returns": returns, "dates": returns.index}
    except Exception:
        logger.exception("Failed to fit Markov switching model for %s", yahoo_id)
        return None
