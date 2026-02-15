from django.core.management.base import BaseCommand
import logging
import os
import pandas as pd

from strategy.processor import markov_switch

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fit a Markov switching model on close-price returns for a given ticker"

    def add_arguments(self, parser):
        parser.add_argument("--ticker", required=True, help="yahoo_id / ticker to analyze")
        parser.add_argument("--regimes", type=int, default=2, help="number of regimes")
        parser.add_argument("--start", default=None, help="start date (YYYY-MM-DD)")
        parser.add_argument("--end", default=None, help="end date (YYYY-MM-DD)")
        parser.add_argument("--maxiter", type=int, default=1000, help="max iterations passed to fit()")
        parser.add_argument("--out", default=None, help="optional output CSV path to save regimes and returns")

    def handle(self, *args, **options):
        ticker = options["ticker"]
        regimes = options["regimes"]
        start = options["start"]
        end = options["end"]
        maxiter = options["maxiter"]
        out_path = options.get("out")

        self.stdout.write(f"Fitting Markov model for {ticker} (regimes={regimes})")
        res = markov_switch.fit_markov_switch(
            ticker, k_regimes=regimes, start=start, end=end, maxiter=maxiter, disp=False
        )
        if res is None:
            self.stdout.write(self.style.WARNING(f"No model fitted for {ticker}"))
            return

        regimes = res.get("regimes")
        returns = res.get("returns")
        dates = res.get("dates")
        self.stdout.write(self.style.SUCCESS(f"Fitted model for {ticker}; regimes length={len(regimes)}"))

        if out_path:
            try:
                # ensure directory exists
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                df = pd.DataFrame({"date": pd.to_datetime(dates), "return": returns.values, "regime": regimes})
                df.to_csv(out_path, index=False)
                self.stdout.write(self.style.SUCCESS(f"Saved regimes+returns to {out_path}"))
            except Exception:
                logger.exception("Failed to save CSV to %s", out_path)
                self.stdout.write(self.style.ERROR(f"Failed to save CSV to {out_path}"))
