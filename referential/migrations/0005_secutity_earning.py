# Generated by Django 3.1 on 2020-09-13 03:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('referential', '0004_securitydescription_market_cap'),
    ]

    operations = [
        migrations.CreateModel(
            name='secutity_earning',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('yahoo_id', models.CharField(max_length=50, unique=True)),
                ('earning_date', models.DateField()),
            ],
            options={
                'verbose_name': 'earning',
            },
        ),
    ]
