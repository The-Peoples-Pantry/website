# Generated by Django 3.1.2 on 2021-04-13 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0073_auto_20210412_1443'),
    ]

    operations = [
        migrations.AddField(
            model_name='mealrequest',
            name='pickup_details',
            field=models.TextField(blank=True, help_text='List any details the deliverer might need to know for pickup', verbose_name='Pickup details'),
        ),
    ]