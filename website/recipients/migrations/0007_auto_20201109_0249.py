# Generated by Django 3.1.2 on 2020-11-09 02:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recipients", "0006_auto_20201109_0008"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mealrequest",
            name="delivery_details",
            field=models.TextField(
                blank=True,
                help_text="Please provide us with any details we may need to know for the delivery",
                verbose_name="Delivery details",
            ),
        ),
    ]
