from django.contrib import admin

from .models import MealRequest, UpdateNote, Delivery


class MealRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'email',
        'phone_number',
        'city',
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


admin.site.register(MealRequest, MealRequestAdmin)
admin.site.register(UpdateNote, UpdateNoteAdmin)
admin.site.register(Delivery, DeliveryAdmin)
