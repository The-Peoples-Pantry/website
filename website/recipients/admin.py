from django.contrib import admin

from .models import MealRequest, UpdateNote, Delivery

admin.site.register(MealRequest)
admin.site.register(UpdateNote)
admin.site.register(Delivery)
