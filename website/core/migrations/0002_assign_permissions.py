# Generated by Django 3.1.2 on 2020-11-17 00:45

from django.db import migrations
from django.core.management.sql import emit_post_migrate_signal


GROUP_PERMISSIONS = {
    "Chefs": [
        "add_delivery",
        "view_delivery",
        "view_mealrequest",
    ],
    "Deliverers": [
        "add_delivery",
        "view_delivery",
        "view_mealrequest",
    ],
    "Organizers": [
        "add_delivery",
        "change_delivery",
        "delete_delivery",
        "view_delivery",
        "add_mealrequest",
        "change_mealrequest",
        "delete_mealrequest",
        "view_mealrequest",
        "add_updatenote",
        "change_updatenote",
        "delete_updatenote",
        "view_updatenote",
    ],
}


def assign_group_permissions(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    db_alias = schema_editor.connection.alias

    # Workaround to ensure content types for Permissions have been loaded
    # After this, we can safely lookup and assign Permissions
    emit_post_migrate_signal(verbosity=0, interactive=False, db=db_alias)

    for group_name, permissions in GROUP_PERMISSIONS.items():
        group, _ = Group.objects.using(db_alias).get_or_create(name=group_name)
        for permission_name in permissions:
            permission = Permission.objects.get(codename=permission_name)
            group.permissions.add(permission)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("recipients", "0010_auto_20201116_2146"),
    ]

    operations = [
        # DEPRECATED
        # This migration is now purposely commented out to deprecate it
        # The new method of assigning permissions is with the management command
        #  migrations.RunPython(assign_group_permissions)
    ]
