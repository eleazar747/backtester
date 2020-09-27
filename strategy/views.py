from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
import pandas as pd
# Create your views here.
from .processor.backtest import backtester_next10d,computeResultBacktest
def view_backtest(request):
    backtester_next10d()
    return HttpResponse("Ok")

def view_computeResultBacktest(request):
    result=computeResultBacktest()
    return HttpResponse(result.to_html())