import math
from django import template

register = template.Library()


@register.simple_tag()
def ceiling(value):
    if value is None:
        return None
    return math.ceil(value)
