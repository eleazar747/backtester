from django.test import TestCase
from datetime import date

import pandas as pd
from unittest.mock import patch

from .models import strategy_backtested
from .processor.backtest import _run_indicator_trades, _store_indicator_backtest, _generate_indicator_backtests, _combine_signals
from .processor.signals import supertrend_signal


class BacktestSignalTests(TestCase):
    def test_run_indicator_trades_normalizes_dates(self):
        prices = pd.Series(
            [10.0, 11.0, 12.0, 11.5],
            index=pd.to_datetime([
                '2026-01-01T00:00:00+08:00',
                '2026-01-02T00:00:00+08:00',
                '2026-01-03T00:00:00+08:00',
                '2026-01-04T00:00:00+08:00',
            ]),
        )
        signals = pd.Series([1, 0, 0, -1], index=prices.index)

        trades = _run_indicator_trades(prices, signals)

        self.assertEqual(len(trades), 1)
        self.assertIsInstance(trades[0][0], date)
        self.assertIsInstance(trades[0][1], date)
        self.assertEqual(trades[0][0], date(2026, 1, 1))
        self.assertEqual(trades[0][1], date(2026, 1, 4))

    def test_store_indicator_backtest_persists_dates(self):
        trades = [(date(2026, 1, 1), date(2026, 1, 4), 10.0, 12.0)]

        _store_indicator_backtest('TEST', 'rsi', 14, 30, trades)

        saved = strategy_backtested.objects.get(
            name='indicator_2y',
            yahoo_id='TEST',
            indicator_name='rsi',
        )
        self.assertEqual(saved.buy_date, date(2026, 1, 1))
        self.assertEqual(saved.sell_date, date(2026, 1, 4))
        self.assertEqual(saved.buy_price, 10.0)
        self.assertEqual(saved.sell_price, 12.0)

    def test_supertrend_signal_emits_crosses(self):
        idx = pd.date_range('2026-01-01', periods=40, freq='D')
        close = pd.Series([10 + (i * 0.2) for i in range(20)] + [14 - (i * 0.2) for i in range(20)], index=idx)
        high = close + 0.5
        low = close - 0.5

        _, sig = supertrend_signal(high, low, close, lookback=7, multiplier=2)

        self.assertTrue((sig != 0).any())

    @patch('strategy.processor.backtest._fetch_two_year_history')
    def test_generate_indicator_backtests_returns_all_indicators(self, mock_fetch):
        idx = pd.date_range('2026-01-01', periods=40, freq='D')
        close = pd.Series([10 + (i * 0.2) for i in range(20)] + [14 - (i * 0.2) for i in range(20)], index=idx)
        mock_fetch.return_value = pd.DataFrame({
            'Close': close.values,
            'High': (close + 0.5).values,
            'Low': (close - 0.5).values,
        }, index=idx)

        results = _generate_indicator_backtests('TEST')

        self.assertEqual(
            {r.indicator_name for r in results},
            {
                'rsi',
                'supertrend',
                'macd',
                'ema_cross',
                'ema_trend',
                'bollinger',
                'stochastic',
                'multi_indicator_combo',
                'all_indicators_combo',
            },
        )
        self.assertTrue(any(r.trades for r in results))

    def test_combine_signals_requires_consensus(self):
        idx = pd.date_range('2026-01-01', periods=4, freq='D')
        sig_a = pd.Series([1, 1, -1, 0], index=idx)
        sig_b = pd.Series([1, -1, -1, 0], index=idx)

        combined = _combine_signals([sig_a, sig_b], min_votes=2)

        self.assertEqual(list(combined.values), [1, 0, -1, 0])

    def test_combine_signals_allows_vote_balance_mode(self):
        idx = pd.date_range('2026-01-01', periods=3, freq='D')
        sig_a = pd.Series([1, 1, -1], index=idx)
        sig_b = pd.Series([1, -1, -1], index=idx)
        sig_c = pd.Series([1, 1, 0], index=idx)

        combined = _combine_signals([sig_a, sig_b, sig_c], min_votes=2, allow_opposite_votes=True)

        self.assertEqual(list(combined.values), [1, 0, -1])
