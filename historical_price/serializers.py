from rest_framework import serializers
from .models import historical_price

class securitydescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = historical_price
        fields = ('yahoo_id', 'close_price')