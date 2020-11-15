from django.contrib.auth.mixins import LoginRequiredMixin
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from recipients.models import MealRequest
from .tables import MealRequestTable
from .filters import MealRequestFilter


class IndexView(LoginRequiredMixin, SingleTableMixin, FilterView):
    model = MealRequest
    table_class = MealRequestTable
    filterset_class = MealRequestFilter
    template_name = "volunteers/index.html"
