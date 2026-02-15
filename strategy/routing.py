from django.urls import path
from .consumers import BacktestConsumer

websocket_urlpatterns = [
    path('ws/backtest/', BacktestConsumer.as_asgi()),
]