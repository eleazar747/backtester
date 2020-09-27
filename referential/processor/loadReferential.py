import pandas as pd
from ..models import securitydescription
import yfinance as yf
 
def loadStock():
    stocks=pd.read_excel("C:\\Users\\eleazar\git\\stockmarket\\referential\\processor\\referential_1.xlsx")
    print(stocks)
    
    for i in range(0, stocks['Full Ticker'].count()):
        try:
            ticker = yf.Ticker(stocks['Full Ticker'][i])
            infos=ticker.info
            name=infos['shortName']
            print('download ' + str(name))
            country=infos['country']
            sectorLevel1=infos['sector']
            industryLevel1=infos['industry']
            marketCap=infos['marketCap']
            marketPlace=infos['market']
            securitydescription.objects.update_or_create(product_id=stocks['Full Ticker'][i], 
                                                         defaults=dict(yahoo_id=stocks['Full Ticker'][i], name=name,
                                                                       industry_level_1=industryLevel1,ticker=stocks['Full Ticker'][i],
                                                                       market_place=marketPlace, sector_level_1=sectorLevel1, market_cap=marketCap,
                                                                       country=country))
        except Exception as e:
            print("problem to retrieve stock " + str(stocks['Full Ticker'][i]) + " "+str(e))                                                  
