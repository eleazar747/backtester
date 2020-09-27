from rest_framework import serializers
from .models import securitydescription

class securitydescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = securitydescription
        fields = ('yahoo_id', 'name')