from pathlib import Path

import pandas as pd
import yfinance as yf

from ..models import securitydescription


WORKBOOK_NAMES = ("referential_1.xlsx", "referential.xlsx")


def _resolve_workbook_path():
    base_dir = Path(__file__).resolve().parent
    for workbook_name in WORKBOOK_NAMES:
        workbook_path = base_dir / workbook_name
        if workbook_path.exists():
            return workbook_path

    raise FileNotFoundError(f"No referential workbook found in {base_dir}")


def _clean_text(value, default=""):
    if pd.isna(value):
        return default
    text = str(value).strip()
    return text if text else default


def _clean_float(value):
    if pd.isna(value):
        return None
    return float(value)


def loadStock():
    stocks = pd.read_excel(_resolve_workbook_path())
    print(stocks)

    for _, stock in stocks.iterrows():
        full_ticker = _clean_text(stock.get("Full Ticker"))
        if not full_ticker:
            continue

        try:
            ticker = yf.Ticker(full_ticker)
            infos = ticker.info
            print("download " + str(full_ticker))

            name = _clean_text(infos.get("shortName"), _clean_text(stock.get("Name"), full_ticker))
            country = _clean_text(infos.get("country"))
            sector_level_1 = _clean_text(infos.get("sector"))
            industry_level_1 = _clean_text(infos.get("industry"), _clean_text(stock.get("Industry")))
            market_cap = _clean_float(infos.get("marketCap"))
            if market_cap is None:
                market_cap = _clean_float(stock.get("Market cap"))
            market_place = _clean_text(infos.get("market"), _clean_text(stock.get("Exchange")))
            ticker_symbol = _clean_text(stock.get("Ticker symbol"), full_ticker)

            securitydescription.objects.update_or_create(
                product_id=full_ticker,
                defaults=dict(
                    yahoo_id=full_ticker,
                    ticker=ticker_symbol,
                    ric=full_ticker,
                    sector_level_1=sector_level_1,
                    sector_level_2="",
                    industry_level_1=industry_level_1,
                    industry_level_2="",
                    name=name,
                    rating_SP="",
                    rating_Fish="",
                    rating_Moodys="",
                    market_place=market_place,
                    benchmark_1="",
                    benchmark_2="",
                    benchmark_3="",
                    country=country,
                    market_cap=market_cap,
                    isin="",
                ),
            )
        except Exception as e:
            print("problem to retrieve stock " + str(full_ticker) + " " + str(e))
