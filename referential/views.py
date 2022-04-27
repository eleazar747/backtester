from django.shortcuts import render
from .processor.loadReferential import loadStock
from django.http import HttpResponse, JsonResponse
# Create your views here.
from django.shortcuts import render, HttpResponseRedirect
import pandas as pd
from .models import securitydescription
from .serializers import securitydescriptionSerializer
from historical_price.models import historical_price
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from strategy.processor.backtest import computeResultBacktest ,computeResultBacktestbigdrop
def loadstatic(request):
    loadStock()
    return HttpResponse("OK")


@csrf_exempt
def get_data(request):
    data = securitydescription.objects.all()
    if request.method == 'GET':
        serializer = securitydescriptionSerializer(data, many=True)
        return JsonResponse(serializer.data, safe=False)
    
    
def viewDashboard(request):
    data2=securitydescription.objects.all().values()
    print(data2)
    
    histo=historical_price.objects.filter(yahoo_id='BTC').order_by('spot_date').values()
    df=pd.DataFrame(histo)
    labels=[]
    chartdata=[]
    for i in range(0, df['spot_date'].count()):
        labels.append(str(df['spot_date'][i]))
        chartdata.append(df['close_price'][i])
         
    chartLabel = "Historical Price"
     
    data ={ 
                     "labels":labels, 
                     "chartLabel":chartLabel, 
                     "chartdata":chartdata,
                     'name': 'BTC', 
             } 
    
    
    return render(request, 'dashboard.html',{'data2': data2, 'labels': labels,'histo': histo, 'data': data})

def viewsWelcome(request):
    data2=securitydescription.objects.filter(industry_level_1='Gambling').values()
    df=pd.DataFrame(data2)
    return HttpResponse(df.to_html())

def view_backtester(request):
    data2=computeResultBacktestbigdrop()
    
    data_result=data2.values()
    histo=historical_price.objects.filter(yahoo_id='ALK').order_by('spot_date').values()
    df=pd.DataFrame(histo)
    labels=[]
    chartdata=[]
    for i in range(0, df['spot_date'].count()):
        labels.append(str(df['spot_date'][i]))
        chartdata.append(df['close_price'][i])
         
    chartLabel = "Historical Price"
     
    data ={ 
                     "labels":labels, 
                     "chartLabel":chartLabel, 
                     "chartdata":chartdata,
                     'name': 'ALK', 
             } 
    
    
    return render(request, 'backtest_result.html',{'data_result': data_result, 'labels': labels,'histo': histo, 'data': data})
