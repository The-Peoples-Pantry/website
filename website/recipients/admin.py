import uuid
from django.contrib import admin, messages
from .models import MealRequest, GroceryRequest, UpdateNote, Delivery, Status
from django.utils.translation import ngettext

class StatusFilter(admin.SimpleListFilter):
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return Status.choices

    def queryset(self, request, queryset):
        if self.value() and self.value() != 'Unconfirmed':
            matching_uuids = [delivery.request.uuid for delivery in Delivery.objects.filter(status=self.value())]
            queryset = queryset.filter(uuid__in=matching_uuids)
        elif self.value() == 'Unconfirmed':
            matching_uuids = [delivery.request.uuid for delivery in Delivery.objects.all()]
            queryset = queryset.exclude(uuid__in=matching_uuids)

        return queryset


class LandlineFilter(admin.SimpleListFilter):
    title = 'Phone type'
    parameter_name = 'landline'

    def lookups(self, request, model_admin):
        return (
            (False, 'Landline'),
            (True, 'Cellphone')
        )

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(can_receive_texts=self.value())
        return queryset



class DeliveryInline(admin.TabularInline):
    model = Delivery
    extra = 0


class UpdateNoteInline(admin.StackedInline):
    model = UpdateNote
    extra = 0


class MealRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'email',
        'phone_number',
        'landline',
        'city',
        'created_at',
        'delivery_date',
        'status',
        'landline',
    )
    list_filter = (
        'delivery_date',
        StatusFilter,
        LandlineFilter,
        'created_at',
    )
    inlines = (
        DeliveryInline,
        UpdateNoteInline,
    )
    actions = (
        'confirm',
        'copy'
    )


    def landline(self, obj):
        return 'No' if obj.can_receive_texts else 'Yes'
    landline.short_description = "Landline"

    def confirm(self, request, queryset):
        confirmed_uuids = [delivery.request.uuid for delivery in Delivery.objects.filter(status=Status.DATE_CONFIRMED)]
        queryset = queryset.exclude(uuid__in=confirmed_uuids)
        updated = 0

        # Updated all deliveries associated with given request
        for meal_request in queryset:
            updated += Delivery.objects.filter(request=meal_request).update(status=Status.DATE_CONFIRMED)

        if updated:
            self.message_user(request, ngettext(
                "%d delivery has been confirmed with recipient",
                "%d deliveries have been confirmed with recipient",
                updated,
            ) % updated, messages.SUCCESS)
        else:
            self.message_user(
                request,
                "No updates were made",
                messages.WARNING
            )
    confirm.short_description = "Mark deliveries as confirmed with recipient"


    def copy(self, request, queryset):
        ids = []
        for meal_request in queryset:
            meal_request.pk = None
            meal_request.uuid = uuid.uuid4()
            meal_request.delivery_date = None
            meal_request.save()
            ids.append(meal_request.id)

        self.message_user(request, ngettext(
            "%d copied meal request has been created with ID %s",
            "%d copied meal requests have been created with IDs %s",
            len(ids),
        ) % (len(ids), (", ").join(str(id) for id in ids)), messages.SUCCESS)
    copy.short_description = "Create a copy of selected meal request"


class GroceryRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'email',
        'phone_number',
        'city',
        'vegetables',
        'fruits',
        'protein',
        'grains',
        'condiments',
        'dairy',
        'created_at',
        'delivery_date',
    )
    list_filter = (
        'delivery_date',
        'created_at',
    )


class UpdateNoteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'note',
        'request_id',
        'created_at',
    )
    list_filter = (
        'created_at',
    )


class DeliveryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request',
        'status',
        'chef',
        'deliverer',
        'pickup_start',
        'pickup_end',
        'dropoff_start',
        'dropoff_end',
        'container_delivery',
    )
    list_filter = (
        'status',
        'container_delivery',
    )


admin.site.register(GroceryRequest, GroceryRequestAdmin)
admin.site.register(MealRequest, MealRequestAdmin)
admin.site.register(UpdateNote, UpdateNoteAdmin)
admin.site.register(Delivery, DeliveryAdmin)
