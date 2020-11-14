from django_filters import FilterSet
from recipients.models import MealRequest


class MealRequestFilter(FilterSet):
    class Meta:
        model = MealRequest
        fields = ('city', 'num_adults')
