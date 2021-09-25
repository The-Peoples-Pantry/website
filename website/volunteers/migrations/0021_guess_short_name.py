# Update all Volunteers with a guess at their "short name"
# We expose short name so that people can set a preference
# We're going to "guess" that their short name is just the first name
# That's not perfect cause of https://www.kalzumeus.com/2010/06/17/falsehoods-programmers-believe-about-names/
# But we need to do something short term to improve the privacy a bit more
from django.db import migrations


def guess_short_name(apps, schema_editor):
    Volunteer = apps.get_model("volunteers", "Volunteer")
    db_alias = schema_editor.connection.alias

    for volunteer in Volunteer.objects.using(db_alias).all():
        if not volunteer.name:
            continue
        volunteer.short_name = volunteer.name.split(" ")[0]
        volunteer.save()


class Migration(migrations.Migration):

    dependencies = [
        ("volunteers", "0020_update_multiselectfields"),
    ]

    operations = [
        migrations.RunPython(guess_short_name),
    ]
