from django.db import models


class historical_price(models.Model):
    
    yahoo_id=models.CharField(null=False, max_length=50)
    open_price=models.FloatField(null=True)
    close_price=models.FloatField(null=True)
    high_price=models.FloatField(null=True)
    low_price=models.FloatField(null=True)
    spot_date=models.DateField(null=True)
    price_change_1d=models.FloatField(null=True)
    price_change_2d=models.FloatField(null=True)
    price_change_5d=models.FloatField(null=True)
    price_change_10d=models.FloatField(null=True)
    price_change_15d=models.FloatField(null=True)
    price_change_30d=models.FloatField(null=True)
    std_30d=models.FloatField(null=True)
    mean_30d=models.FloatField(null=True)
    dividend=models.FloatField(null=True)
    volume=models.FloatField(null=True)
    mean_volume_30d=models.FloatField(null=True)
    std_volume_30d=models.FloatField(null=True)
    volume_var=models.FloatField(null=True)
    ranking_change_1d=models.FloatField(null=True)
    ranking_change_2d=models.FloatField(null=True)
    ranking_change_5d=models.FloatField(null=True)
    ranking_change_10d=models.FloatField(null=True)
    ranking_change_15d=models.FloatField(null=True)
    ranking_change_30d=models.FloatField(null=True)
    ranking_std_30d=models.FloatField(null=True)
    ranking_mean_30d=models.FloatField(null=True)
    
    
    class Meta:
         verbose_name = "historical price"
        
    def __str__(self):
        self.yahoo_id
        
        
class income_statement(models.Model):
    yahoo_id=models.CharField(null=False, max_length=50)
    ref_date=models.DateField(null=True)
    revenue=models.FloatField(null=False)
    cost_revenue=models.FloatField(null=False)
    netIncome=models.FloatField(null=False)
    operatingExpenses=models.FloatField(null=False)
    eps=models.FloatField(null=False)
    ebitda=models.FloatField(null=False)
    interestExpense=models.FloatField(null=False)
    researchAndDevelopmentExpenses=models.FloatField(null=False)
    fillingDate=models.DateField(null=False)
    acceptedDate=models.DateField(null=False)
    period=models.CharField(null=False, max_length=50)
    
    class Meta:
        verbose_name="income statement"
    
    def __str__(self):
        self.yahoo_id
    
class balance_sheet(models.Model):
    yahoo_id=models.CharField(null=False, max_length=50)
    ref_date=models.DateField(null=True)
    current_liabilities=models.FloatField(null=False)
    non_current_liabilities=models.FloatField(null=False)
    stockholder_equity=models.FloatField(null=False)
    
    class Meta:
        verbose_name="balance sheet"
        
    def __str__(self):
        self.yahoo_id

class fx_historical_price(models.Model):
    
    yahoo_id=models.CharField(null=False, max_length=50)
    open_price=models.FloatField(null=True)
    close_price=models.FloatField(null=True)
    high_price=models.FloatField(null=True)
    low_price=models.FloatField(null=True)
    spot_date=models.DateField(null=True)
    
    class Meta:
        verbose_name="fx historical price"
        
    def __str__(self):
        self.yahoo_id
        
class commodities_historical_price(models.Model):
    yahoo_id=models.CharField(null=False, max_length=50)
    open_price=models.FloatField(null=True)
    close_price=models.FloatField(null=True)
    high_price=models.FloatField(null=True)
    low_price=models.FloatField(null=True)
    spot_date=models.DateField(null=True)
    
    class Meta:
        verbose_name="commodity historical price"
        
    def __str__(self):
        self.yahoo_id