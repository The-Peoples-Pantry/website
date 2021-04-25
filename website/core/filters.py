import django_filters
from .forms import DateField


class DateFilter(django_filters.DateFilter):
    field_class = DateField
