from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from django.conf import settings


class Command(BaseCommand):
    help = "Set group permissions to a hardcoded list"

    def handle(self, *args, **options):
        self.stdout.write("Setting all group permissions")

        for group_name, permission_names in settings.GROUP_PERMISSIONS.items():
            group = Group.objects.get(name=group_name)
            group.permissions.clear()
            self.stdout.write(f"Cleared all permissions for {group_name}")

            for permission_name in permission_names:
                permission = Permission.objects.get(codename=permission_name)
                group.permissions.add(permission)
                self.stdout.write(f"Added {permission_name} permission to {group_name}")

        self.stdout.write(
            self.style.SUCCESS("Successfully reset all group permissions")
        )
