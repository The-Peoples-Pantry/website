# Generated by Django 3.1.2 on 2021-04-02 14:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipients', '0065_remove_groceryrequest_physical_gift_card'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groceryrequest',
            name='uuid',
        ),
        migrations.RemoveField(
            model_name='mealdelivery',
            name='uuid',
        ),
        migrations.RemoveField(
            model_name='mealrequest',
            name='uuid',
        ),
    ]