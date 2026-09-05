from historical_price.models import historical_price
from referential.models import securitydescription
import pandas as pd
import yfinance as yf
from dataclasses import dataclass
from datetime import datetime,timedelta
from ..models import strategy_backtested
from hamcrest.core.core.isnone import none
from numpy import lookfor
from django.conf.locale import nb
import math
import statistics
from historical_price.processor.historical_price import getHistopricebyId as Histo
from strategy.processor.signals import (
    compute_rsi,
    rsi_signal,
    supertrend_signal,
    macd_signal,
    ema_cross_signal,
    ema_trend_signal,
    bollinger_signal,
    stochastic_signal,
)


@dataclass
class IndicatorBacktestSet:
    ticker: str
    indicator_name: str
    param_1: float
    param_2: float
    trades: list
    param_3: float = None


def _fetch_two_year_history(ticker_symbol):
    df = pd.DataFrame(yf.Ticker(str(ticker_symbol)).history(period='3y', auto_adjust=True))
    if df.empty:
        return df

    df = df.reset_index()
    date_col = 'Date' if 'Date' in df.columns else 'Datetime'
    return df.set_index(date_col).sort_index()


def _run_indicator_trades(prices, signals):
    position = False
    buy_date = None
    buy_price = None
    trades = []

    for date, price, signal in zip(prices.index, prices.values, signals.values):
        trade_date = pd.Timestamp(date).date()
        if signal == 1 and not position:
            position = True
            buy_date = trade_date
            buy_price = price
        elif signal == -1 and position:
            trades.append((buy_date, trade_date, buy_price, price))
            position = False
            buy_date = None
            buy_price = None

    if position and buy_date is not None:
        last_date = pd.Timestamp(prices.index[-1]).date()
        last_price = prices.iloc[-1]
        trades.append((buy_date, last_date, buy_price, last_price))

    return trades


def _combine_signals(signals, min_votes, allow_opposite_votes=False):
    signal_df = pd.concat(signals, axis=1).fillna(0).astype(int)
    buy_votes = (signal_df == 1).sum(axis=1)
    sell_votes = (signal_df == -1).sum(axis=1)

    combined = pd.Series(0, index=signal_df.index, dtype=int)
    if allow_opposite_votes:
        vote_balance = buy_votes - sell_votes
        combined[vote_balance >= min_votes] = 1
        combined[vote_balance <= -min_votes] = -1
    else:
        combined[(buy_votes >= min_votes) & (sell_votes == 0)] = 1
        combined[(sell_votes >= min_votes) & (buy_votes == 0)] = -1
    return combined


def _generate_indicator_backtests(ticker):
    df = _fetch_two_year_history(ticker)
    if df.empty or len(df) < 30:
        return []

    close = df['Close']
    high = df['High']
    low = df['Low']

    rsi = compute_rsi(close, period=14)
    rsi_sig = rsi_signal(rsi)
    rsi_trades = _run_indicator_trades(close, rsi_sig)

    _, st_sig = supertrend_signal(high, low, close, lookback=10, multiplier=3)
    st_trades = _run_indicator_trades(close, st_sig)
    _, _, macd_sig = macd_signal(close, fast=12, slow=26, signal_span=9)
    macd_trades = _run_indicator_trades(close, macd_sig)

    _, _, ema_sig = ema_cross_signal(close, fast=20, slow=50)
    ema_trades = _run_indicator_trades(close, ema_sig)

    _, _, _, trend_sig = ema_trend_signal(close, fast_period=20, slow_period=50, momentum_period=10)
    trend_trades = _run_indicator_trades(close, trend_sig)

    _, _, _, bb_sig = bollinger_signal(close, window=20, num_std=2)
    bb_trades = _run_indicator_trades(close, bb_sig)

    _, _, stochastic_sig = stochastic_signal(high, low, close, k_period=14, d_period=3)
    stochastic_trades = _run_indicator_trades(close, stochastic_sig)

    indicator_sets = [
        IndicatorBacktestSet(ticker=ticker, indicator_name='rsi', param_1=14, param_2=30, trades=rsi_trades),
        IndicatorBacktestSet(ticker=ticker, indicator_name='supertrend', param_1=10, param_2=3, trades=st_trades),
        IndicatorBacktestSet(ticker=ticker, indicator_name='macd', param_1=12, param_2=26, trades=macd_trades),
        IndicatorBacktestSet(ticker=ticker, indicator_name='ema_cross', param_1=20, param_2=50, trades=ema_trades),
        IndicatorBacktestSet(ticker=ticker, indicator_name='ema_trend', param_1=20, param_2=50, param_3=10, trades=trend_trades),
        IndicatorBacktestSet(ticker=ticker, indicator_name='bollinger', param_1=20, param_2=2, trades=bb_trades),
        IndicatorBacktestSet(ticker=ticker, indicator_name='stochastic', param_1=14, param_2=3, trades=stochastic_trades),
    ]

    combo_signals = [rsi_sig, st_sig, macd_sig, ema_sig, trend_sig, bb_sig, stochastic_sig]
    majority_votes = 3
    combo_majority_sig = _combine_signals(
        combo_signals,
        min_votes=majority_votes,
        allow_opposite_votes=True,
    )
    combo_majority_trades = _run_indicator_trades(close, combo_majority_sig)
    combo_all_sig = _combine_signals(combo_signals, min_votes=len(combo_signals))
    combo_all_trades = _run_indicator_trades(close, combo_all_sig)

    indicator_sets.extend([
        IndicatorBacktestSet(
            ticker=ticker,
            indicator_name='multi_indicator_combo',
            param_1=majority_votes,
            param_2=len(combo_signals),
            trades=combo_majority_trades,
        ),
        IndicatorBacktestSet(
            ticker=ticker,
            indicator_name='all_indicators_combo',
            param_1=len(combo_signals),
            param_2=len(combo_signals),
            trades=combo_all_trades,
        ),
    ])

    return indicator_sets


def _store_indicator_backtest(ticker, indicator_name, param_1, param_2, trades, param_3=None):
    strategy_backtested.objects.filter(
        yahoo_id=ticker,
        name='indicator_2y',
        indicator_name=indicator_name,
        param_1=param_1,
        param_2=param_2,
        param_3=param_3,
    ).delete()

    if not trades:
        strategy_backtested.objects.create(
            yahoo_id=ticker,
            name='indicator_2y',
            indicator_name=indicator_name,
            param_1=param_1,
            param_2=param_2,
            param_3=param_3,
            buy_date=None,
            sell_date=None,
            buy_price=None,
            sell_price=None,
        )
        return

    for buy_date, sell_date, buy_price, sell_price in trades:
        strategy_backtested.objects.create(
            yahoo_id=ticker,
            name='indicator_2y',
            indicator_name=indicator_name,
            param_1=param_1,
            param_2=param_2,
            param_3=param_3,
            buy_date=buy_date,
            sell_date=sell_date,
            buy_price=buy_price,
            sell_price=sell_price,
        )


def backtester_indicators_last_2y():
    list_stock = pd.DataFrame(securitydescription.objects.all().values())
    if list_stock.empty:
        print('No securities available for indicator backtest')
        return

    print('Running indicator backtest from live 2-year Yahoo history')

    for ticker in list_stock['yahoo_id']:
        backtest_sets = _generate_indicator_backtests(ticker)
        if not backtest_sets:
            print('Skipping ' + str(ticker) + ' due to insufficient history')
            continue

        for backtest_set in backtest_sets:
            _store_indicator_backtest(
                backtest_set.ticker,
                backtest_set.indicator_name,
                backtest_set.param_1,
                backtest_set.param_2,
                backtest_set.trades,
                backtest_set.param_3,
            )
            print(
                'Backtested '
                + backtest_set.indicator_name.upper()
                + ' for '
                + str(backtest_set.ticker)
                + ' with '
                + str(len(backtest_set.trades))
                + ' trades'
            )

    print('Indicator backtest complete')
def backtester_next10d():
    
    list_stock=securitydescription.objects.values_list('yahoo_id')
    print(list_stock)
    delta = timedelta(days=1)
    strat_name='10d'
    for j in range(1,10):
        level=j/100
        start_date = datetime(2020, 9, 1)
        end_date = datetime.today()
        while start_date <= end_date:
            print(start_date)
            histo=historical_price.objects.filter(price_change_5d__gte=level, price_change_10d__gte=level, price_change_15d__lte=level, spot_date=start_date).values()
            dfHisto=pd.DataFrame(histo)
            if not dfHisto.empty:
                for i in range(0,dfHisto['yahoo_id'].count()):
                    
                    start_check_date=start_date+timedelta(days=1)
                    end_check_date=start_date+timedelta(days=10)
                    
                    histo_check=historical_price.objects.filter(yahoo_id=str(dfHisto['yahoo_id'][i]), spot_date__gte=start_check_date, spot_date__lte=end_check_date).values()
                    dfHisto_check=pd.DataFrame(histo_check)
                    if not dfHisto_check.empty:
                        
                        result=dfHisto_check.loc[dfHisto_check['close_price']>dfHisto['close_price'][i]]
                        if not result.empty:
                            
                            result.reset_index(inplace=True)
                            print("Found Exit for "+ str(dfHisto['yahoo_id'][i]) +" buy on " + str(start_date) +" at " + str(dfHisto['close_price'][i]) + " sell on " + str(result['spot_date'][0]) + " at " + str(result['close_price'][0]))
                            strategy_backtested.objects.update_or_create(yahoo_id=dfHisto['yahoo_id'][i],name=strat_name, param_1=level, param_2=level, param_3=level, buy_date=start_date,
                                                                          defaults=dict(yahoo_id=dfHisto['yahoo_id'][i], name=strat_name,
                                                                                        param_1=level,param_2=level,param_3=level, buy_date=start_date, sell_date=result['spot_date'][0],
                                                                                        buy_price=dfHisto['close_price'][i], sell_price=result['close_price'][0])) 
                        else:
                            strategy_backtested.objects.update_or_create(yahoo_id=dfHisto['yahoo_id'][i],name=strat_name, param_1=level, param_2=level, param_3=level, buy_date=start_date,
                                                                          defaults=dict(yahoo_id=dfHisto['yahoo_id'][i], name=strat_name,
                                                                                        param_1=level,param_2=level,param_3=level, buy_date=start_date,
                                                                                        buy_price=dfHisto['close_price'][i]))
                    else:
                        strategy_backtested.objects.update_or_create(yahoo_id=dfHisto['yahoo_id'][i],name=strat_name, param_1=level, param_2=level, param_3=level, buy_date=start_date,
                                                                          defaults=dict(yahoo_id=dfHisto['yahoo_id'][i], name=strat_name,
                                                                                        param_1=level,param_2=level,param_3=level, buy_date=start_date,
                                                                                        buy_price=dfHisto['close_price'][i]))
            else:
                print("No signal on " + str(start_date))
            start_date += delta
def backtester_next10d_coin():
    
    list_stock=securitydescription.objects.filter(yahoo_id='BTC').values()
    print(list_stock)
    delta = timedelta(days=1)
    strat_name='10d'
    for j in range(1,10):
        level=j/100
        start_date = datetime(2020, 9, 1)
        end_date = datetime.today()
        while start_date <= end_date:
            print(start_date)
            histo=historical_price.objects.filter(price_change_5d__gte=level, price_change_10d__gte=level, price_change_15d__lte=level, spot_date=start_date, yahoo_id='BTC').values()
            dfHisto=pd.DataFrame(histo)
            if not dfHisto.empty:
                for i in range(0,dfHisto['yahoo_id'].count()):
                    
                    start_check_date=start_date+timedelta(days=1)
                    end_check_date=start_date+timedelta(days=10)
                    
                    histo_check=historical_price.objects.filter(yahoo_id=str(dfHisto['yahoo_id'][i]), spot_date__gte=start_check_date, spot_date__lte=end_check_date).values()
                    dfHisto_check=pd.DataFrame(histo_check)
                    if not dfHisto_check.empty:
                        
                        result=dfHisto_check.loc[dfHisto_check['close_price']>dfHisto['close_price'][i]]
                        if not result.empty:
                            
                            result.reset_index(inplace=True)
                            print("Found Exit for "+ str(dfHisto['yahoo_id'][i]) +" buy on " + str(start_date) +" at " + str(dfHisto['close_price'][i]) + " sell on " + str(result['spot_date'][0]) + " at " + str(result['close_price'][0]))
                            strategy_backtested.objects.update_or_create(yahoo_id=dfHisto['yahoo_id'][i],name=strat_name, param_1=level, param_2=level, param_3=level, buy_date=start_date,
                                                                          defaults=dict(yahoo_id=dfHisto['yahoo_id'][i], name=strat_name,
                                                                                        param_1=level,param_2=level,param_3=level, buy_date=start_date, sell_date=result['spot_date'][0],
                                                                                        buy_price=dfHisto['close_price'][i], sell_price=result['close_price'][0])) 
                        else:
                            strategy_backtested.objects.update_or_create(yahoo_id=dfHisto['yahoo_id'][i],name=strat_name, param_1=level, param_2=level, param_3=level, buy_date=start_date,
                                                                          defaults=dict(yahoo_id=dfHisto['yahoo_id'][i], name=strat_name,
                                                                                        param_1=level,param_2=level,param_3=level, buy_date=start_date,
                                                                                        buy_price=dfHisto['close_price'][i]))
                    else:
                        strategy_backtested.objects.update_or_create(yahoo_id=dfHisto['yahoo_id'][i],name=strat_name, param_1=level, param_2=level, param_3=level, buy_date=start_date,
                                                                          defaults=dict(yahoo_id=dfHisto['yahoo_id'][i], name=strat_name,
                                                                                        param_1=level,param_2=level,param_3=level, buy_date=start_date,
                                                                                        buy_price=dfHisto['close_price'][i]))
            else:
                print("No signal on " + str(start_date))
            start_date += delta
class backtest_result():
    def __init__(self,ticker):
        self.name=ticker
        
    def update_ath(self,nb_transaction, winner,pct_winner, buy_date, sell_date, buy_price, sell_price, last_price,param_level):
        self.nb_transaction_ath=nb_transaction
        self.winner_ath=winner=winner
        self.pct_winner_ath=pct_winner
        self.last_buy_date=buy_date
        self.last_buy_price=buy_price
        self.last_price=last_price
        self.last_sell_date=sell_date
        self.last_sell_price=sell_price
        self.param_level=param_level
    
    def update_3m(self,nb_transaction, winner,pct_winner):
        self.nb_transaction_3m=nb_transaction
        self.winner_3m=winner=winner
        self.pct_winner_3m=pct_winner

    def update_6m(self,nb_transaction, winner,pct_winner):
        self.nb_transaction_6m=nb_transaction
        self.winner_6m=winner=winner
        self.pct_winner_6m=pct_winner
        
    def update_ytd(self,nb_transaction, winner,pct_winner):
        self.nb_transaction_ytd=nb_transaction
        self.winner_ytd=winner=winner
        self.pct_winner_ytd=pct_winner
        
    def to_dict(self):
        return {
            "Name": self.name,
            "Level": self.param_level,
            "Nb_Transaction": self.nb_transaction,
            "Winner": self.winner,
            "Pct_winner": self.pct_winner,
            "last_Buy_Date": self.last_buy_date,
            "last_Sell_Date": self.last_sell_date,
            "nb_Transaction_6M":self.nb_transaction_6m,
            "Winner_6M": self.winner_6m,
            "Pct_winner_3M": self.pct_winner_3m,
            "Pct_winner_6M": self.pct_winner_6m,
            "Pct_winner_ytd": self.pct_winner_ytd,
        }
  
def computeResultBacktest():
    list_stock=pd.DataFrame(securitydescription.objects.all().values())
    strat_name='10d'
    d_result=dict();
    param_level=0.05
    for ticker in list_stock['yahoo_id']:
        d_result[ticker]=computeSingleTicker(ticker, strat_name, param_level)
                
    return d_result
            
def computeResult(df):
    nb_transaction=df.buy_date.count()
    looser=df.loc[df['sell_date'].isnull()].buy_date.count()
    winner=nb_transaction-looser
    pct_winner=round(winner/nb_transaction*100,2)
    pct_looser=round(looser/nb_transaction*100,2)
    return nb_transaction, winner, pct_winner

def computeSingleTicker(ticker, strat_name, param_level):
    result_ath=strategy_backtested.objects.filter(yahoo_id=ticker, name=strat_name, param_1=param_level).values()
    result_3m=strategy_backtested.objects.filter(yahoo_id=ticker, name=strat_name, buy_date__gte='2020-07-01', param_1=param_level).values()
    result_6m=strategy_backtested.objects.filter(yahoo_id=ticker, name=strat_name, buy_date__gte='2020-04-01', param_1=param_level).values()
    result_ytd=strategy_backtested.objects.filter(yahoo_id=ticker, name=strat_name, buy_date__gte='2020-01-01', param_1=param_level).values()
    df=pd.DataFrame(result_ath)
    try:
        last_date=pd.DataFrame(historical_price.objects.filter(yahoo_id=ticker).order_by('-id').values())
        last_price=last_date['close_price'][0]
    except:
        last_price=0
    print(last_price)
    resultat=backtest_result(ticker)
    if not df.empty:
        nb_transaction, winner, pct_winner=computeResult(df)
        last_buy_date=df.buy_date[len(df.buy_date)-1]
        last_buy_date_f=last_buy_date.strftime("%Y-%m-%d")
        buy_price=df.buy_price[len(df.buy_price)-1]
        last_sell_date=df.sell_date[len(df.sell_date)-1]
        last_sell_date_f=last_sell_date.strftime("%Y-%m-%d")
        sell_price=df.sell_price[len(df.sell_price)-1]

        resultat.update_ath(nb_transaction, winner, pct_winner,last_buy_date_f,last_sell_date_f, buy_price,sell_price,last_price, param_level)
    else:
         resultat.update_ath(0,0,0,'2000-01-01','2000-01-01',0, 0,0,param_level)
    
    # 3m RESULTAT
    df=pd.DataFrame(result_3m)
    if not df.empty:
        nb_transaction, winner, pct_winner=computeResult(df)
        if resultat!=None:
            resultat.update_3m(nb_transaction,winner,pct_winner)
    
    df=pd.DataFrame(result_6m)
    if not df.empty:
        nb_transaction, winner, pct_winner=computeResult(df)
        if resultat!=None:
            resultat.update_6m(nb_transaction,winner,pct_winner)
    
    df=pd.DataFrame(result_ytd)
    if not df.empty:
        nb_transaction, winner, pct_winner=computeResult(df)
        if resultat!=None:
            resultat.update_ytd(nb_transaction,winner,pct_winner)
    return resultat

def meanreversion():
    start_check_date=datetime(2021, 1, 1)
    end_check_date=datetime.today()
    start_check_date5=datetime.today()-timedelta(days=5)
    start_check_date10=datetime.today()-timedelta(days=10)
    start_check_date20=datetime.today()-timedelta(days=20)
    start_check_date30=datetime.today()-timedelta(days=30)

    list_stock=pd.DataFrame(securitydescription.objects.all().values())
    for ticker in list_stock['yahoo_id']:
        print(ticker)
        histo_check=pd.DataFrame(historical_price.objects.filter(yahoo_id=str(ticker), spot_date__gte=start_check_date, spot_date__lte=end_check_date).values())
        histo_check5=pd.DataFrame(historical_price.objects.filter(yahoo_id=str(ticker), spot_date__gte=start_check_date5, spot_date__lte=end_check_date).values())
        histo_check10=pd.DataFrame(historical_price.objects.filter(yahoo_id=str(ticker), spot_date__gte=start_check_date10, spot_date__lte=end_check_date).values())
        histo_check20=pd.DataFrame(historical_price.objects.filter(yahoo_id=str(ticker), spot_date__gte=start_check_date20, spot_date__lte=end_check_date).values())
        histo_check30=pd.DataFrame(historical_price.objects.filter(yahoo_id=str(ticker), spot_date__gte=start_check_date30, spot_date__lte=end_check_date).values())
        print(histo_check)

        avg=statistics.mean(histo_check.price_change_1d)
        std=statistics.stdev(histo_check.price_change_1d)
        avg5=statistics.mean(histo_check.price_change_1d)
        std5=statistics.stdev(histo_check.price_change_1d)
        avg10=statistics.mean(histo_check.price_change_1d)
        std10=statistics.stdev(histo_check.price_change_1d)
        avg20=statistics.mean(histo_check.price_change_1d)
        std20=statistics.stdev(histo_check.price_change_1d)
        avg30=statistics.mean(histo_check.price_change_1d)
        std30=statistics.stdev(histo_check.price_change_1d)


def backtester_bigdrop():
    
    list_stock=securitydescription.objects.values_list('yahoo_id')
    print(list_stock)
    delta = timedelta(days=1)
    strat_name='bigdrop'
    for j in range(1,10):
        level1=-j/50
        level2=level1/2
        start_date = datetime(2020, 9, 1)
        end_date = datetime.today()
        while start_date <= end_date:
            print(start_date)
            histo=historical_price.objects.filter(price_change_1d__lte=level1, price_change_10d__gte=level2, spot_date=start_date).values()
            dfHisto=pd.DataFrame(histo)
            if not dfHisto.empty:
                for i in range(0,dfHisto['yahoo_id'].count()):
                    
                    start_check_date=start_date+timedelta(days=1)
                    end_check_date=start_date+timedelta(days=10)
                    
                    histo_check=historical_price.objects.filter(yahoo_id=str(dfHisto['yahoo_id'][i]), spot_date__gte=start_check_date, spot_date__lte=end_check_date).values()
                    dfHisto_check=pd.DataFrame(histo_check)
                    if not dfHisto_check.empty:
                        
                        result=dfHisto_check.loc[dfHisto_check['close_price']<dfHisto['close_price'][i]]
                        if not result.empty:
                            
                            result.reset_index(inplace=True)
                            print("Found Exit for "+ str(dfHisto['yahoo_id'][i]) +" sell on " + str(start_date) +" at " + str(dfHisto['close_price'][i]) + " buy on " + str(result['spot_date'][0]) + " at " + str(result['close_price'][0]))
                            strategy_backtested.objects.update_or_create(yahoo_id=dfHisto['yahoo_id'][i],name=strat_name, param_1=level1, param_2=level2, param_3=None, sell_date=start_date,
                                                                          defaults=dict(yahoo_id=dfHisto['yahoo_id'][i], name=strat_name,
                                                                                        param_1=level1,param_2=level2,param_3=None, buy_date=result['spot_date'][0], sell_date=start_date,
                                                                                        buy_price=dfHisto['close_price'][0], sell_price=result['close_price'][1])) 
                        else:
                            strategy_backtested.objects.update_or_create(yahoo_id=dfHisto['yahoo_id'][i],name=strat_name, param_1=level1, param_2=level2, param_3=None, sell_date=start_date,
                                                                          defaults=dict(yahoo_id=dfHisto['yahoo_id'][i], name=strat_name,
                                                                                        param_1=level1,param_2=level2,param_3=None, sell_date=start_date,
                                                                                        sell_price=dfHisto['close_price'][i]))
                    else:
                        strategy_backtested.objects.update_or_create(yahoo_id=dfHisto['yahoo_id'][i],name=strat_name, param_1=level1, param_2=level2, param_3=None, sell_date=start_date,
                                                                          defaults=dict(yahoo_id=dfHisto['yahoo_id'][i], name=strat_name,
                                                                                        param_1=level1,param_2=level2,param_3=None, sell_date=start_date,
                                                                                        sell_price=dfHisto['close_price'][i]))
            else:
                print("No signal on " + str(start_date))
            start_date += delta


def computeResultBacktestbigdrop():
    list_stock=pd.DataFrame(securitydescription.objects.all().values())
    strat_name='bigdrop'
    d_result=dict();
    param_level=-0.08
    for ticker in list_stock['yahoo_id']:
        d_result[ticker]=computeSingleTicker(ticker, strat_name, param_level)
                
    return d_result