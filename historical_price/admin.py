from django.contrib import admin
from .models import historical_price

class HistoPriceAdmin(admin.ModelAdmin):
   list_display   = ('yahoo_id', 'spot_date', 'close_price')

# Register your models here.
admin.site.register(historical_price,HistoPriceAdmin)
