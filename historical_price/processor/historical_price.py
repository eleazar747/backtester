import yfinance as yf
import pandas as pd
from referential.models import securitydescription 
from ..models import historical_price
from datetime import datetime
def retrieve_price():
	print('start download from yahoo finance')
	symbol=securitydescription.objects.all().values()
	df=pd.DataFrame(symbol)
	end_date=datetime.now().date()
	print(end_date)
	for i in range(0, df['yahoo_id'].count()):
		
		try:
			ticker = yf.Ticker(df['yahoo_id'][i])	
			data=ticker.history(start="2021-03-01", end=end_date, auto_adjust = True)
			dfHisto=pd.DataFrame(data)
			dfHisto.reset_index(inplace=True)
			dfHisto['price_change_1d']=(dfHisto['Close']/dfHisto['Close'].shift(1)-1)
			dfHisto['price_change_2d']=(dfHisto['Close']/dfHisto['Close'].shift(2)-1)
			dfHisto['price_change_5d']=(dfHisto['Close']/dfHisto['Close'].shift(5)-1)
			dfHisto['price_change_10d']=(dfHisto['Close']/dfHisto['Close'].shift(10)-1)
			dfHisto['price_change_15d']=(dfHisto['Close']/dfHisto['Close'].shift(15)-1)
			dfHisto['price_change_30d']=(dfHisto['Close']/dfHisto['Close'].shift(30)-1)
			
			dfHisto['mean_volume_30d']=dfHisto['Volume'].rolling(30).mean();
			dfHisto['std_volume_30d']=dfHisto['Volume'].rolling(30).std();
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
			
			for j in range(0, dfHisto['Date'].count()):
				historical_price.objects.update_or_create(yahoo_id=df['yahoo_id'][i], spot_date=dfHisto['Date'][j], defaults=dict(
					open_price=dfHisto['Open'][j],low_price=dfHisto['Low'][j],high_price=dfHisto['High'][j],close_price=dfHisto['Close'][j],
					volume=dfHisto['Volume'][j],dividend=dfHisto['Dividends'][j],price_change_1d=dfHisto['price_change_1d'][j],price_change_2d=dfHisto['price_change_2d'][j]
					,price_change_5d=dfHisto['price_change_5d'][j],price_change_10d=dfHisto['price_change_10d'][j],price_change_15d=dfHisto['price_change_15d'][j]
					,price_change_30d=dfHisto['price_change_30d'][j],mean_30d=dfHisto['mean_30d'][j],std_30d=dfHisto['std_30d'][j]
					,mean_volume_30d=dfHisto['mean_volume_30d'][j],std_volume_30d=dfHisto['std_volume_30d'][j]))
			print("Downloaded : " + str(df['yahoo_id'][i]))
		except Exception as e:
			print("issue with symbol " + str(df['yahoo_id'][i]) + str(e))
		
	print(symbol)

def getHistopricebyId(ticker):
	resulat=pd.DataFrame(historical_price.object.filter(yahoo_id=ticker))

	return resulat