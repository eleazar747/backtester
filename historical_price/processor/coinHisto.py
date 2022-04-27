import san
import pandas as pd
from ..models import historical_price
def retrieve_price_coin():
	try:
		data = san.get("ohlcv/bitcoin", from_date="2018-01-01", to_date="2021-10-07")
		dfHisto=pd.DataFrame(data)
		dfHisto.reset_index(inplace=True)
		
		dfHisto['price_change_1d']=(dfHisto['closePriceUsd']/dfHisto['closePriceUsd'].shift(1)-1)
		dfHisto['price_change_2d']=(dfHisto['closePriceUsd']/dfHisto['closePriceUsd'].shift(2)-1)
		dfHisto['price_change_5d']=(dfHisto['closePriceUsd']/dfHisto['closePriceUsd'].shift(5)-1)
		dfHisto['price_change_10d']=(dfHisto['closePriceUsd']/dfHisto['closePriceUsd'].shift(10)-1)
		dfHisto['price_change_15d']=(dfHisto['closePriceUsd']/dfHisto['closePriceUsd'].shift(15)-1)
		dfHisto['price_change_30d']=(dfHisto['closePriceUsd']/dfHisto['closePriceUsd'].shift(30)-1)			
		dfHisto['mean_volume_30d']=dfHisto['volume'].rolling(30).mean();
		dfHisto['std_volume_30d']=dfHisto['volume'].rolling(30).std();
		dfHisto['mean_30d']=dfHisto['price_change_1d'].rolling(30).mean()
		dfHisto['std_30d']=dfHisto['price_change_1d'].rolling(30).std()
		dfHisto['ranking_change_1d']=dfHisto['price_change_1d'].rank(ascending=True)
		dfHisto['ranking_change_2d']=dfHisto['price_change_2d'].rank(ascending=True)
		dfHisto['ranking_change_5d']=dfHisto['price_change_5d'].rank(ascending=True)
		dfHisto['ranking_change_10d']=dfHisto['price_change_10d'].rank(ascending=True)
		dfHisto['ranking_change_15d']=dfHisto['price_change_15d'].rank(ascending=True)
		dfHisto['ranking_change_30d']=dfHisto['price_change_30d'].rank(ascending=True)
		dfHisto['ranking_std_30d']=dfHisto['std_30d'].rank(ascending=True)
		dfHisto['ranking_mean_30d']=dfHisto['mean_30d'].rank(ascending=True)
		print(dfHisto)
		for j in range(0, dfHisto['datetime'].count()):
			historical_price.objects.update_or_create(yahoo_id='BTC', spot_date=dfHisto['datetime'][j], defaults=dict(
				open_price=dfHisto['openPriceUsd'][j],low_price=dfHisto['lowPriceUsd'][j],high_price=dfHisto['highPriceUsd'][j],close_price=dfHisto['closePriceUsd'][j],
				volume=dfHisto['volume'][j],dividend=0,price_change_1d=dfHisto['price_change_1d'][j],price_change_2d=dfHisto['price_change_2d'][j]
				,price_change_5d=dfHisto['price_change_5d'][j],price_change_10d=dfHisto['price_change_10d'][j],price_change_15d=dfHisto['price_change_15d'][j]
				,price_change_30d=dfHisto['price_change_30d'][j],mean_30d=dfHisto['mean_30d'][j],std_30d=dfHisto['std_30d'][j]
				,mean_volume_30d=dfHisto['mean_volume_30d'][j],std_volume_30d=dfHisto['std_volume_30d'][j]))
			print("Downloaded : BTC")
	except Exception as e:
		print("issue with symbol BTC")