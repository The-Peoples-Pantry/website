import django_tables2 as tables
from recipients.models import MealRequest


class MealRequestTable(tables.Table):
    class Meta:
        model = MealRequest
        attrs = {"class": "table-responsive"}
