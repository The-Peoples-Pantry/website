# Update all the Volunteer fields that have been converted to MultiSelectField
# Original multiple choice widget stores them as "['one','two','three']"
# MultiSelectField stores them as "one,two,three"
# Need to run this data migration to convert between formats
from django.db import migrations
import ast

VOLUNTEER_FIELDS = (
    'cooking_prefs',
    'days_available',
    'food_types',
    'organizer_teams',
    'transportation_options',
)

VOLUNTEER_APPLICATION_FIELDS = (
    'organizer_teams',
)


def is_affected(field):
    """field would be ["[one", "two", "three]"] if affected"""
    if not isinstance(field, list):
        return False
    return any('[' in entry for entry in field)


def fixed(field):
    return ast.literal_eval(",".join(field))


def update_volunteer_fields(apps, schema_editor):
    Volunteer = apps.get_model('volunteers', 'Volunteer')
    db_alias = schema_editor.connection.alias

    for volunteer in Volunteer.objects.using(db_alias).all():
        affected = False
        for field_name in VOLUNTEER_FIELDS:
            field = getattr(volunteer, field_name)
            if is_affected(field):
                affected = True
                setattr(volunteer, field_name, fixed(field))
        if affected:
            volunteer.save()


def update_volunteerapplication_fields(apps, schema_editor):
    VolunteerApplication = apps.get_model('volunteers', 'VolunteerApplication')
    db_alias = schema_editor.connection.alias

    for volunteer_application in VolunteerApplication.objects.using(db_alias).all():
        if is_affected(volunteer_application.organizer_teams):
            volunteer_application.organizer_teams = fixed(volunteer_application.organizer_teams)
            volunteer_application.save()


class Migration(migrations.Migration):

    dependencies = [
        ('volunteers', '0019_auto_20210214_0906'),
    ]

    operations = [
        migrations.RunPython(update_volunteer_fields),
        migrations.RunPython(update_volunteerapplication_fields),
    ]
