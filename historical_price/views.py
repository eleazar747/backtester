from django.shortcuts import render
from django.http import HttpResponse
from .processor.historical_price import retrieve_price
from .models import historical_price
# Create your views here.
import pandas as pd
def loadhistoprice(request):
    retrieve_price()
    return HttpResponse("OK")

def strategy(request):
    queryset=historical_price.objects.filter(price_change_2d__gte=0.1, price_change_2d__lte=0.15,spot_date='2020-09-11').values()
    df=pd.DataFrame(queryset)
    return HttpResponse(df.to_html())
    
    
