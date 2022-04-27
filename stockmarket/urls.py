"""stockmarket URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import path
from django.contrib import admin
from django.conf.urls import url
from referential import views
from historical_price import views as viewshisto
from django.views.generic.base import TemplateView
from strategy import views as viewsBacktest


urlpatterns = [
    path('admin/', admin.site.urls),
    path('loadstatic',views.loadstatic),
    path('loadhistoprice', viewshisto.loadhistoprice),
    path('dashboard/',views.viewDashboard),
    path('welcome/', views.viewsWelcome),
    path('strategy', viewshisto.strategy),
    path('backtester',viewsBacktest.view_backtest),
    path('histo',views.viewsWelcome),
    path('result/',views.view_backtester ),
    path('meanreversion',viewsBacktest.view_meanreversion ),
    path('statregy_supertrend',viewsBacktest.view_supertrendtest),
    path('bigdrop', viewsBacktest.view_bigdrop),
    path('strategy_drop', viewsBacktest.view_backtestbigdrop),
    path('load_histo_coin',viewshisto.loadHistoCoin),
    path('bactester_coin',viewsBacktest.view_backtest_coin)

]
