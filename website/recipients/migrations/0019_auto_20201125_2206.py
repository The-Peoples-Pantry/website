# Generated by Django 3.1.2 on 2020-11-25 22:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0018_auto_20201125_0124'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='groceryrequest',
            options={'verbose_name': 'Groceries'},
        ),
        migrations.AlterModelOptions(
            name='mealrequest',
            options={'verbose_name': 'Meal'},
        ),
    ]