from django.contrib import admin, messages
from django.utils.translation import ngettext

from .models import Volunteer, VolunteerApplication


class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'role', 'approved')
    list_filter = ('approved', 'role')
    ordering = ('approved', )
    actions = ('approve', )

    def approve(self, request, queryset):
        updated = queryset.filter(approved=False).update(approved=True)
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


admin.site.register(Volunteer)
admin.site.register(VolunteerApplication, VolunteerApplicationAdmin)
