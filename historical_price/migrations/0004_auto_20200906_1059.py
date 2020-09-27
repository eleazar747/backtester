# Generated by Django 3.1 on 2020-09-06 02:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('historical_price', '0003_historical_price_volume'),
    ]

    operations = [
        migrations.AddField(
            model_name='historical_price',
            name='mean_30d',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='historical_price',
            name='mean_volume_30d',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='historical_price',
            name='std_30d',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='historical_price',
            name='std_volume_30d',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='historical_price',
            name='volume_var',
            field=models.FloatField(null=True),
        ),
    ]