from django.contrib import admin, messages
from django.db import transaction
from django.utils.translation import ngettext

from core.models import group_names
from .models import Volunteer, VolunteerApplication


class VolunteerAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'groups', 'city', 'training_complete')

    def groups(self, obj):
        return group_names(obj.user)


class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'role', 'approved')
    list_filter = ('approved', 'role')
    ordering = ('approved', )
    actions = ('approve', )

    def name(self, app):
        return app.user.volunteer.name
    name.short_description = 'Name'

    @transaction.atomic
    def approve(self, request, queryset):
        # De-select any values that have already been approved
        queryset = queryset.filter(approved=False)

        # Approve each application and keep count
        # If the application has already been approved it won't count towards the total
        updated = 0
        for application in queryset:
            if application.approve():
                updated += 1

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
