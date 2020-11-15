import django_tables2 as tables
from recipients.models import MealRequest


class WideColumn(tables.Column):
    """Use a wider-than-usual column for the table field"""
    def __init__(self, **kwargs):
        attrs = {'cell': {'style': 'min-width: 300px'}}
        super().__init__(attrs=attrs, **kwargs)


class MealRequestTable(tables.Table):
    notes = WideColumn()
    food_allergies = WideColumn()
    food_preferences = WideColumn()
    delivery_details = WideColumn()

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
