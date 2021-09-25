# Copy the data in MealDelivery fields into MealRequest
# We will shortly be deprecating the MealDelivery model
from django.db import migrations


def copy_data_from_meal_delivery_to_meal_request(apps, schema_editor):
    MealRequest = apps.get_model("recipients", "MealRequest")
    db_alias = schema_editor.connection.alias

    for meal_request in MealRequest.objects.using(db_alias).all():
        if not hasattr(meal_request, "delivery"):
            continue

        meal_request.chef = meal_request.delivery.chef
        meal_request.deliverer = meal_request.delivery.deliverer
        meal_request.status = meal_request.delivery.status
        meal_request.delivery_date = meal_request.delivery.date
        meal_request.pickup_start = meal_request.delivery.pickup_start
        meal_request.pickup_end = meal_request.delivery.pickup_end
        meal_request.dropoff_start = meal_request.delivery.dropoff_start
        meal_request.dropoff_end = meal_request.delivery.dropoff_end
        meal_request.meal = meal_request.delivery.meal
        meal_request.save()


def remove_meal_delivery_info_from_meal_request(apps, schema_editor):
    MealRequest = apps.get_model("recipients", "MealRequest")
    db_alias = schema_editor.connection.alias

    for meal_request in MealRequest.objects.using(db_alias).all():
        meal_request.chef = None
        meal_request.deliverer = None
        meal_request.status = MealRequest._meta.get_field("status").get_default()
        meal_request.delivery_date = None
        meal_request.pickup_start = None
        meal_request.pickup_end = None
        meal_request.dropoff_start = None
        meal_request.dropoff_end = None
        meal_request.meal = ""
        meal_request.save()


class Migration(migrations.Migration):

    dependencies = [
        ("recipients", "0068_auto_20210411_1008"),
    ]

    operations = [
        migrations.RunPython(
            copy_data_from_meal_delivery_to_meal_request,
            reverse_code=remove_meal_delivery_info_from_meal_request,
        ),
    ]
