from django import forms
from django_filters import FilterSet, DateFilter
from recipients.models import MealRequest, Delivery

class DateInput(forms.DateInput):
    input_type = 'date'

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


class ChefSignupFilter(FilterSet):
    class Meta:
        form = HiddenValidationForm
        model = MealRequest
        fields = {
            'city': ['exact'],
            'num_adults': ['lt'],
            'num_children': ['lt'],
            'dairy_free': ['exact'],
            'gluten_free': ['exact'],
            'halal': ['exact'],
            'low_carb': ['exact'],
            'vegan': ['exact'],
            'vegetarian': ['exact'],
        }


class DeliverySignupFilter(FilterSet):
    request__delivery_date = DateFilter(
        widget=DateInput()
    )

    def __init__(self, *args, **kwargs):
       super(DeliverySignupFilter, self).__init__(*args, **kwargs)
       self.filters['request__city'].label="City"
       self.filters['request__num_adults__lt'].label="Number of adults in the household is less than"
       self.filters['request__num_children__lt'].label="Number of children in the household is less than"
       self.filters['request__delivery_date'].label="Delivery date"

    class Meta:
        form = HiddenValidationForm
        model = Delivery
        fields = {
            'request__city': ['exact'],
            'request__num_adults': ['lt'],
            'request__num_children': ['lt'],
            'request__delivery_date': ['exact'],
        }