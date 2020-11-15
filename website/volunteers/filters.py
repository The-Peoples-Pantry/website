from django import forms
from django_filters import FilterSet
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
    bound_css_class = ''


class MealRequestFilter(FilterSet):
    class Meta:
        form = HiddenValidationForm
        model = MealRequest
        fields = ('city', 'num_adults')
