from django.db import models

# Create your models here.
class strategy_backtested(models.Model):
    name=models.CharField(max_length=100, null=False)
    yahoo_id=models.CharField(max_length=100, null=False)
    param_1=models.FloatField(null=True)
    param_2=models.FloatField(null=True)
    param_3=models.FloatField(null=True)
    param_4=models.FloatField(null=True)
    param_3=models.FloatField(null=True)
    buy_date=models.DateField(null=True)
    sell_date=models.DateField(null=True)
    buy_price=models.FloatField(null=True)
    sell_price=models.FloatField(null=True)
    def __str__(self):
        print(self.name)
    
    class Meta:
        verbose_name = "Strategy"