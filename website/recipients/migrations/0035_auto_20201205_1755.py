# Generated by Django 3.1.2 on 2020-12-05 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0034_auto_20201204_2012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groceryrequest',
            name='can_meet_for_delivery',
            field=models.BooleanField(help_text='We care about safety. Thus, we try to avoid delivery volunteers going into buildings or houses. Would you / the person requiring support be able to meet the delivery person in the lobby or door of the residence, while wearing protective equipment such as masks?', verbose_name='Able to meet delivery driver'),
        ),
        migrations.AlterField(
            model_name='mealrequest',
            name='can_meet_for_delivery',
            field=models.BooleanField(help_text='We care about safety. Thus, we try to avoid delivery volunteers going into buildings or houses. Would you / the person requiring support be able to meet the delivery person in the lobby or door of the residence, while wearing protective equipment such as masks?', verbose_name='Able to meet delivery driver'),
        ),
    ]