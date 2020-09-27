# Generated by Django 3.1 on 2020-09-13 03:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('historical_price', '0004_auto_20200906_1059'),
    ]

    operations = [
        migrations.CreateModel(
            name='balance_sheet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('yahoo_id', models.CharField(max_length=50)),
                ('ref_date', models.DateField(null=True)),
                ('current_liabilities', models.FloatField()),
                ('non_current_liabilities', models.FloatField()),
                ('stockholder_equity', models.FloatField()),
            ],
            options={
                'verbose_name': 'balance sheet',
            },
        ),
        migrations.CreateModel(
            name='income_statement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('yahoo_id', models.CharField(max_length=50)),
                ('ref_date', models.DateField(null=True)),
                ('revenue', models.FloatField()),
                ('cost_revenue', models.FloatField()),
            ],
            options={
                'verbose_name': 'income statement',
            },
        ),
    ]
