# Generated by Django 3.1.2 on 2021-03-03 23:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0056_auto_20210303_0925'),
    ]

    operations = [
        migrations.AddField(
            model_name='groceryrequest',
            name='covid',
            field=models.BooleanField(default=False, help_text='Have you been diagnosed with, or are you currently experiencing any symptoms of COVID-19? Such as fever, cough, difficulty breathing, or chest pain?', verbose_name='COVID-19'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='mealrequest',
            name='covid',
            field=models.BooleanField(default=False, help_text='Have you been diagnosed with, or are you currently experiencing any symptoms of COVID-19? Such as fever, cough, difficulty breathing, or chest pain?', verbose_name='COVID-19'),
            preserve_default=False,
        ),
    ]