from django import template
import website.maps

register = template.Library()


@register.simple_tag()
def distance(a, b):
    """
    Calculates the distance between two instances a and b
    Expects a and b to be instances of a model that subclasses AddressMixin
    """
    return website.maps.distance(a.coordinates, b.coordinates)
