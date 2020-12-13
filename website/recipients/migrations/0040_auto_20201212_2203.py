# Generated by Django 3.1.2 on 2020-12-13 03:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0039_auto_20201212_0025'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groceryrequest',
            name='can_meet_for_delivery',
            field=models.BooleanField(help_text='Please confirm that you / the person requiring support will be able to meet the delivery person in the lobby or door of the residence, while wearing protective equipment such as masks?', verbose_name='Able to meet delivery driver'),
        ),
        migrations.AlterField(
            model_name='mealrequest',
            name='can_meet_for_delivery',
            field=models.BooleanField(help_text='Please confirm that you / the person requiring support will be able to meet the delivery person in the lobby or door of the residence, while wearing protective equipment such as masks?', verbose_name='Able to meet delivery driver'),
        ),
    ]
