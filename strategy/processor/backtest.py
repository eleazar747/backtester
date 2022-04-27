from historical_price.models import historical_price
from referential.models import securitydescription
import pandas as pd
from datetime import datetime,timedelta
from ..models import strategy_backtested
from hamcrest.core.core.isnone import none
from numpy import lookfor
from django.conf.locale import nb
import math
import statistics
from historical_price.processor.historical_price import getHistopricebyId as Histo
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