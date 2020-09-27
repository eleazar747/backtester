from historical_price.models import historical_price
from referential.models import securitydescription
import pandas as pd
from datetime import datetime,timedelta
from ..models import strategy_backtested
from hamcrest.core.core.isnone import none
from numpy import lookfor
from django.conf.locale import nb
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

class backtest_result():
    def __init__(self,ticker,nb_transaction, winner,looser,pct_winner, buy_date):
        self.name=ticker
        self.nb_transaction=nb_transaction
        self.winner=winner
        self.looser=looser
        self.pct_winner=pct_winner
        self.last_buy_date=buy_date
        
    def to_dict(self):
        return {
            "Name": self.name,
            "Nb_Transaction": self.nb_transaction,
            "Winner": self.winner,
            "Pct_winner": self.pct_winner,
        }
  
def computeResultBacktest():
    list_stock=pd.DataFrame(securitydescription.objects.all().values())
    strat_name='10d'
    d_result=[]
    d_result_3m=[]
    for ticker in list_stock['yahoo_id']:
        result=strategy_backtested.objects.filter(yahoo_id=ticker, name=strat_name, param_1=0.05).values()
        df=pd.DataFrame(result)
        if not df.empty:
            nb_transaction=df.buy_date.count()
            looser=df.loc[df['sell_date'].isnull()].buy_date.count()
            winner=nb_transaction-looser
            pct_winner=round(winner/nb_transaction*100,2)
            pct_looser=looser/nb_transaction
            d_result.append(backtest_result(ticker,nb_transaction, winner, looser, pct_winner))
        else:
            d_result.append(backtest_result(ticker,0,0,0,0))
    resultict = [resultat.to_dict() for resultat in d_result]
    df=pd.DataFrame(resultict)
    
    for ticker in list_stock['yahoo_id']:
        result=strategy_backtested.objects.filter(yahoo_id=ticker, name=strat_name, buy_date__gte='2020-01-01', param_1=0.05).values()
        df2=pd.DataFrame(result)
        if not df2.empty:
            nb_transaction=df2.buy_date.count()
            looser=df2.loc[df2['sell_date'].isnull()].buy_date.count()
            winner=nb_transaction-looser
            pct_winner=round(winner/nb_transaction*100,2)
            pct_looser=looser/nb_transaction
            d_result_3m.append(backtest_result(ticker,nb_transaction, winner, looser, pct_winner))
        else:
            d_result_3m.append(backtest_result(ticker,0, 0, 0, 0))
    
    result_dict_3m=[resultat.to_dict() for resultat in d_result_3m]
    df2=pd.DataFrame(result_dict_3m)
    df_result=df.merge(df2, how='inner', on='Name')
    print(df_result)
    return df_result
            
            
            

     