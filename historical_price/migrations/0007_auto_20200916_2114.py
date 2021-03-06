# Generated by Django 3.1 on 2020-09-16 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('historical_price', '0006_historical_price_ranking_change_5d'),
    ]

    operations = [
        migrations.AddField(
            model_name='historical_price',
            name='ranking_change_10d',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='historical_price',
            name='ranking_change_15d',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='historical_price',
            name='ranking_change_1d',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='historical_price',
            name='ranking_change_2d',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='historical_price',
            name='ranking_change_30d',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='historical_price',
            name='ranking_mean_30d',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='historical_price',
            name='ranking_std_30d',
            field=models.FloatField(null=True),
        ),
    ]
