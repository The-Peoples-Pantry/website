import re
from django.db import migrations


def format_phone_number(phone_number):
    return re.sub(r"[^0-9]", "", phone_number)


def format_phone_numbers(apps, schema_editor):
    GroceryRequest = apps.get_model("recipients", "GroceryRequest")
    MealRequest = apps.get_model("recipients", "MealRequest")
    db_alias = schema_editor.connection.alias

    for req in GroceryRequest.objects.using(db_alias).all():
        req.phone_number = format_phone_number(req.phone_number)
        req.requester_phone_number = format_phone_number(req.requester_phone_number)
        req.save()

    for req in MealRequest.objects.using(db_alias).all():
        req.phone_number = format_phone_number(req.phone_number)
        req.requester_phone_number = format_phone_number(req.requester_phone_number)
        req.save()


class Migration(migrations.Migration):

    dependencies = [
        ("recipients", "0061_auto_20210314_1315"),
    ]

    operations = [
        migrations.RunPython(format_phone_numbers),
    ]
