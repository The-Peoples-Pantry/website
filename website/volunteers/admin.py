from django.contrib import admin, messages
from django.db import transaction
from django.utils.translation import ngettext

from core.admin import user_link
from core.models import group_names
from .models import Volunteer, VolunteerApplication


class VolunteerAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'groups', 'city', 'training_complete', 'is_staff')
    actions = ('remove_permissions',)

    def groups(self, obj):
        return group_names(obj.user)

    def is_staff(self, obj):
        return obj.user.is_staff
    is_staff.boolean = True

    @transaction.atomic
    def remove_permissions(self, request, queryset):
        updated = 0

        for volunteer in queryset:
            if (volunteer.user == request.user):
                self.message_user(
                    request,
                    "You cannot remove your own permissions, as that might prevent you from seeing this page",
                    messages.WARNING
                )
            elif not volunteer.user.is_staff:
                volunteer.remove_permissions()
                updated += 1

        if updated:
            self.message_user(request, ngettext(
                "Permissions have been removed from %d user.",
                "Permissions have been removed from %d users.",
                updated,
            ) % updated, messages.SUCCESS)
        else:
            self.message_user(
                request,
                "All selected volunteers are staff (contact an admin to change this)",
                messages.WARNING
            )
    remove_permissions.short_description = "Remove selected non-staff volunteers from ALL groups"


class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = ('app', 'name', 'user', 'role', 'approved')
    list_filter = ('approved', 'role')
    ordering = ('approved', )
    actions = ('approve', )

    def name(self, application):
        return user_link(application.user)
    name.short_description = 'Name'

    def app(self, application):
        return 'Edit application'
    app.short_description = 'Application'

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
