from django import template
from volunteers.models import Volunteer

register = template.Library()

@register.filter(name='get_volunteer')
def get_volunteer(user, prop):
    return getattr(Volunteer.objects.get(user=user), prop)
