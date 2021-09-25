import re
from django.db import migrations


def format_phone_number(phone_number):
    return re.sub(r"[^0-9]", "", phone_number)


def format_phone_numbers(apps, schema_editor):
    Volunteer = apps.get_model("volunteers", "Volunteer")
    db_alias = schema_editor.connection.alias

    for volunteer in Volunteer.objects.using(db_alias).all():
        volunteer.phone_number = format_phone_number(volunteer.phone_number)
        volunteer.save()


class Migration(migrations.Migration):

    dependencies = [
        ("volunteers", "0022_auto_20210314_1315"),
    ]

    operations = [
        migrations.RunPython(format_phone_numbers),
    ]
