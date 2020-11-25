# Manual migration
from django.db import migrations
from django.core.management.sql import emit_post_migrate_signal

def assign_group_permission(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    db_alias = schema_editor.connection.alias

    # Workaround to ensure content types for Permissions have been loaded
    # After this, we can safely lookup and assign Permissions
    emit_post_migrate_signal(verbosity=0, interactive=False, db=db_alias)

    group = Group.objects.using(db_alias).get(name='Chefs')
    permission = Permission.objects.get(codename='change_mealrequest')
    group.permissions.add(permission)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_assign_permissions'),
        ('recipients', '0018_auto_20201125_0124'),
    ]

    operations = [
        migrations.RunPython(assign_group_permission)
    ]