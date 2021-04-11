# Generated by Django 3.1.2 on 2021-04-11 14:08

import core.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipients', '0067_auto_20210408_1519'),
    ]

    operations = [
        migrations.AddField(
            model_name='mealrequest',
            name='chef',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET(core.models.get_sentinel_user), related_name='cooked_meal_requests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='mealrequest',
            name='deliverer',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET(core.models.get_sentinel_user), related_name='delivered_meal_requests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='mealrequest',
            name='delivery_date',
            field=models.DateField(blank=True, null=True, verbose_name='Delivery date'),
        ),
        migrations.AddField(
            model_name='mealrequest',
            name='dropoff_end',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='mealrequest',
            name='dropoff_start',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='mealrequest',
            name='meal',
            field=models.TextField(blank=True, help_text='(Optional) Let us know what you plan on cooking!', verbose_name='Meal'),
        ),
        migrations.AddField(
            model_name='mealrequest',
            name='pickup_end',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='mealrequest',
            name='pickup_start',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='mealrequest',
            name='status',
            field=models.CharField(choices=[('Unconfirmed', 'Unconfirmed'), ('Chef Assigned', 'Chef Assigned'), ('Driver Assigned', 'Driver Assigned'), ('Delivery Date Confirmed', 'Delivery Date Confirmed'), ('Delivered', 'Delivered')], default='Unconfirmed', max_length=256, verbose_name='Status'),
        ),
    ]