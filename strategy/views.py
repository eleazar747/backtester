from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
import pandas as pd
# Create your views here.
from .processor.backtest import backtester_next10d,computeResultBacktest,meanreversion,backtester_bigdrop,computeResultBacktestbigdrop,backtester_next10d_coin
from .processor.supertrendstrat import start_supertrend

def view_backtest(request):
    backtester_next10d()
    return HttpResponse("Ok")

def view_computeResultBacktest(request):
    result=computeResultBacktest()
    print(result)
    return HttpResponse("OK")

def view_meanreversion(request):
    result=meanreversion()
    print(result)
    return HttpResponse("OK")

def view_supertrendtest(request):
    result=start_supertrend()
    print(result)
    return HttpResponse("OK")

def view_bigdrop(request):
    backtester_bigdrop()
    return HttpResponse('OK')

def view_backtestbigdrop(request):
    computeResultBacktestbigdrop()
    return HttpResponse('OK')

def view_backtest_coin(request):
    backtester_next10d_coin()
    return HttpResponse("Ok")