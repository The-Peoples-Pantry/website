from datetime import timedelta
from django import forms
from django_filters import FilterSet, BooleanFilter
from django.utils import timezone

from core.filters import DateFilter
from recipients.models import MealRequest


class HiddenValidationForm(forms.Form):
    """
    Form that will be subclassed by FilterSets to prevent showing fields marked as valid
    Use by assigning to the "form" field of a FilterSet's "Meta" class
    """

    # Used to prevent the is-valid class on valid filters
    # By adding this override, we prevent the green outline and checkmark on filter controls
    # Filters will be pre-generated and so showing them highlighted as "valid" is weird
    # Read more: https://django-bootstrap4.readthedocs.io/en/stable/templatetags.html
    bound_css_class = ""


class ChefSignupFilter(FilterSet):
    urgent = BooleanFilter(
        label="Urgent", field_name="created_at", method="filter_stale"
    )

    def filter_stale(self, queryset, name, value):
        stale_at = timezone.now() - timedelta(days=MealRequest.STALE_AFTER_DAYS)
        if value:
            return queryset.filter(created_at__lte=stale_at)
        else:
            return queryset.filter(created_at__gt=stale_at)

    class Meta:
        form = HiddenValidationForm
        model = MealRequest
        fields = {
            "city": ["exact"],
            "num_adults": ["lt"],
            "num_children": ["lt"],
            "dairy_free": ["exact"],
            "gluten_free": ["exact"],
            "halal": ["exact"],
            "kosher": ["exact"],
            "low_carb": ["exact"],
            "vegan": ["exact"],
            "vegetarian": ["exact"],
        }


class DelivererSignupFilter(FilterSet):
    delivery_date = DateFilter()

    class Meta:
        form = HiddenValidationForm
        model = MealRequest
        fields = {
            "city": ["exact"],
            "delivery_date": ["exact"],
            "num_adults": ["lt"],
            "num_children": ["lt"],
        }
