import django_tables2 as tables
from recipients.models import MealRequest


class MealRequestTable(tables.Table):
    class Meta:
        model = MealRequest
        attrs = {"class": "table table-hover table-responsive"}
        fields = (
            'id',
            'city',
            'notes',
            'num_adults',
            'num_children',
            'children_ages',
            'food_allergies',
            'food_preferences',
            'will_accept_vegan',
            'will_accept_vegetarian',
            'can_meet_for_delivery',
            'delivery_details',
            'available_days',
            'available_time_periods',
            'dairy_free',
            'gluten_free',
            'halal',
            'low_carb',
            'vegan',
            'vegetarian',
        )
