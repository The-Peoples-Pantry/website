# Generated by Django 3.1.2 on 2020-11-23 00:56

import core.models
from django.conf import settings
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipients', '0010_auto_20201116_2146'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='delivery',
            options={'verbose_name_plural': 'deliveries'},
        ),
        migrations.AlterField(
            model_name='delivery',
            name='deliverer',
            field=models.ForeignKey(null=True, on_delete=models.SET(core.models.get_sentinel_user), related_name='assigned_deliverer', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='dropoff_start',
            field=models.TimeField(null=True),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='pickup_end',
            field=models.TimeField(null=True),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='pickup_start',
            field=models.TimeField(null=True),
        ),
        migrations.AlterField(
            model_name='mealrequest',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4),
        ),
    ]