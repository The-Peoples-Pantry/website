from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import GroceryPickupAddress


def user_link(user):
    if user:
        display_text = user.volunteer.name or user
        url = reverse('admin:volunteers_volunteer_change', args=(user.id,))
        return format_html('<a href="%s">%s</a>' % (url, display_text))
    return user


def obj_link(obj, type, **kwargs):
    if obj:
        link_text = kwargs.get('link_text', str(obj))
        url = reverse('admin:recipients_%s_change' % type, args=(obj.id,))
        return format_html('<a href="%s">%s</a>' % (url, link_text))
    return obj


admin.site.register(GroceryPickupAddress)
