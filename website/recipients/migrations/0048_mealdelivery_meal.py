# Generated by Django 3.1.2 on 2021-02-20 13:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0047_auto_20210219_1725'),
    ]

    operations = [
        migrations.AddField(
            model_name='mealdelivery',
            name='meal',
            field=models.TextField(blank=True, help_text='(Optional) Let us know what you plan on cooking!', verbose_name='Meal'),
        ),
    ]