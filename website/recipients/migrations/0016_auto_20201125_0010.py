# Generated by Django 3.1.2 on 2020-11-25 00:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0015_auto_20201124_2352'),
    ]

    operations = [
        migrations.AddField(
            model_name='groceryrequest',
            name='availability',
            field=models.TextField(default='N/A', help_text="Please list the days and times that you're available to receive a delivery", verbose_name='Availability'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='mealrequest',
            name='availability',
            field=models.TextField(default='N/A', help_text="Please list the days and times that you're available to receive a delivery", verbose_name='Availability'),
            preserve_default=False,
        ),
    ]