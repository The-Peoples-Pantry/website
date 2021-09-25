# Generated by Django 3.1.2 on 2021-01-14 23:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recipients", "0043_merge_20201229_1627"),
    ]

    operations = [
        migrations.AlterField(
            model_name="grocerydelivery",
            name="status",
            field=models.CharField(
                choices=[
                    ("Unconfirmed", "Unconfirmed"),
                    ("Chef Assigned", "Chef Assigned"),
                    ("Driver Assigned", "Driver Assigned"),
                    ("Delivery Date Confirmed", "Delivery Date Confirmed"),
                    ("Recipient Rescheduled", "Recipient Rescheduled"),
                    ("Delivered", "Delivered"),
                ],
                default="Unconfirmed",
                max_length=256,
                verbose_name="Status",
            ),
        ),
        migrations.AlterField(
            model_name="mealdelivery",
            name="status",
            field=models.CharField(
                choices=[
                    ("Unconfirmed", "Unconfirmed"),
                    ("Chef Assigned", "Chef Assigned"),
                    ("Driver Assigned", "Driver Assigned"),
                    ("Delivery Date Confirmed", "Delivery Date Confirmed"),
                    ("Recipient Rescheduled", "Recipient Rescheduled"),
                    ("Delivered", "Delivered"),
                ],
                default="Unconfirmed",
                max_length=256,
                verbose_name="Status",
            ),
        ),
    ]
