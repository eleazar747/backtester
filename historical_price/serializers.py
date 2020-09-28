from rest_framework import serializers
from .models import historical_price

class historicalPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = historical_price
        fields = ('yahoo_id', 'close_price', 'open_price', 'high_price', 'low_price', 'spot_date')