from django.contrib.auth.mixins import LoginRequiredMixin
from django_tables2 import SingleTableView
from recipients.models import MealRequest
from .tables import MealRequestTable


class IndexView(LoginRequiredMixin, SingleTableView):
    model = MealRequest
    table_class = MealRequestTable
    template_name = "volunteers/index.html"
