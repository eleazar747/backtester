# Generated by Django 3.1 on 2020-09-06 04:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('referential', '0002_auto_20200830_1620'),
    ]

    operations = [
        migrations.AddField(
            model_name='securitydescription',
            name='country',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='securitydescription',
            name='market_place',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='securitydescription',
            name='name',
            field=models.CharField(max_length=100),
        ),
    ]