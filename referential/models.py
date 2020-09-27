from django.db import models


class securitydescription(models.Model):
    product_id=models.CharField(null=False, max_length=50, unique=True)
    yahoo_id=models.CharField(null=False, max_length=50, unique=True)
    ticker=models.CharField(null=False, max_length=50)
    ric=models.CharField(null=False, max_length=50)
    sector_level_1=models.CharField(null=False, max_length=100)
    sector_level_2=models.CharField(null=False, max_length=100)
    industry_level_1=models.CharField(null=False, max_length=100)
    industry_level_2=models.CharField(null=False, max_length=100)
    name=models.CharField(null=False, max_length=100)
    rating_SP=models.CharField(null=False, max_length=20)
    rating_Fish=models.CharField(null=False, max_length=20)
    rating_Moodys=models.CharField(null=False, max_length=20)
    market_place=models.CharField(null=True, max_length=50)
    benchmark_1=models.CharField(null=False, max_length=50)
    benchmark_2=models.CharField(null=False, max_length=50)
    benchmark_3=models.CharField(null=False, max_length=50)
    country=models.CharField(null=True, max_length=100)
    market_cap=models.FloatField(null=True)
    isin=models.CharField(null=True, max_length=100)
    
    class Meta:
        verbose_name = "Security description"
        
    def __str__(self):
        return self.name

class secutity_earning(models.Model):
    yahoo_id=models.CharField(null=False, max_length=50, unique=True)
    earning_date=models.DateField(null=False)
    earning_estimated=models.FloatField(null=True)
    earning_realized=models.FloatField(null=True)
    
    class Meta:
        verbose_name="Earning Calendar"
        
    def __str__(self):
        print(self.yahoo_id)
        
        
class economic_calendar(models.Model):
    indicator_name=models.CharField(null=False, max_length=50, unique=True)
    importance=models.CharField(null=False, max_length=50)
    estimated=models.FloatField(null=True)
    realized=models.FloatField(null=True)
    
    class Meta:
        verbose_name="Economic calendar"
        
    def __str__(self):
        print(self.yahoo_id)