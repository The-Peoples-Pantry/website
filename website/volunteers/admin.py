from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils.translation import ngettext

from .models import Volunteer, VolunteerApplication


class VolunteerAdmin(admin.ModelAdmin):
    list_display = ('user', 'groups', 'city', 'training_complete')

    def groups(self, obj):
        return list(obj.user.groups.all().values_list('name', flat=True))


class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'role', 'approved')
    list_filter = ('approved', 'role')
    ordering = ('approved', )
    actions = ('approve', )

    @transaction.atomic
    def approve(self, request, queryset):
        # De-select any values that have already been approved
        queryset = queryset.filter(approved=False)

        # Add each user to the appropriate group
        for application in queryset:
            user = application.user
            group = Group.objects.get(name=application.role)
            user.groups.add(group)

        # Mark the applications as approved
        updated = queryset.update(approved=True)

        if updated:
            self.message_user(request, ngettext(
                "%d application was successfully approved.",
                "%d applications were successfully approved.",
                updated,
            ) % updated, messages.SUCCESS)
        else:
            self.message_user(
                request,
                "All selected applications have already been approved",
                messages.WARNING
            )
    approve.short_description = "Mark selected applications as approved"


admin.site.register(Volunteer, VolunteerAdmin)
admin.site.register(VolunteerApplication, VolunteerApplicationAdmin)
