# Generated by Django 3.1 on 2020-08-30 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('historical_price', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='historical_price',
            name='dividend',
            field=models.FloatField(null=True),
        ),
    ]
