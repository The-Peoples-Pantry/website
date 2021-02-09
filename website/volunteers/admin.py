from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils.translation import ngettext


from core.admin import user_link
from core.models import group_names
from .models import Volunteer, VolunteerApplication


class InGroupFilter(admin.SimpleListFilter):
    title = 'Groups'
    parameter_name = 'groups'

    def lookups(self, request, model_admin):
        groups = Group.objects.all().values_list('name', flat=True)
        return zip(groups, groups)

    def queryset(self, request, queryset):
        if self.value():
            queryset = Volunteer.objects.filter(user__groups__name=self.value())
        return queryset


class VolunteerAdmin(admin.ModelAdmin):
    list_display = ('edit_link', 'name', 'user', 'groups', 'organizer_teams', 'city', 'training_complete', 'is_staff')
    actions = ('remove_permissions', 'mark_training_complete')
    list_filter = (InGroupFilter,)
    search_fields = ('name', 'user__email')

    def edit_link(self, obj):
        return 'Edit'
    edit_link.short_description = 'Volunteer'

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

    @transaction.atomic
    def mark_training_complete(self, request, queryset):
        updated = queryset.update(training_complete=True)
        self.message_user(request, ngettext(
            "Training marked as complete for %d user.",
            "Training marked as complete for %d users.",
            updated,
        ) % updated, messages.SUCCESS)
    mark_training_complete.short_description = "Mark training as complete for selected volunteers"


class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = ('app', 'name', 'user', 'role', 'organizer_teams', 'approved')
    list_filter = ('approved', 'role')
    ordering = ('approved', )
    actions = ('approve', )
    search_fields = ('user__volunteer__name', 'user__email')

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
