# Generated by Django 3.1.2 on 2020-11-13 02:06

from django.db import migrations


GROUPS = ['Chefs', 'Deliverers', 'Organizers']


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    db_alias = schema_editor.connection.alias
    Group.objects.using(db_alias).bulk_create([
        Group(name=group_name) for group_name in GROUPS
    ])


def remove_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    db_alias = schema_editor.connection.alias
    Group.objects.using(db_alias).filter(name__in=GROUPS).delete()


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.RunPython(create_groups, remove_groups)
    ]
