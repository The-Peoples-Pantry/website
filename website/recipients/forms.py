from django.forms import ModelForm
from .models import MealRequest


class MealRequestForm(ModelForm):
    class Meta:
        model = MealRequest
        fields = [
            'name',
            'email',
            'phone_number',
            'can_receive_texts',
            'address_1',
            'address_2',
            'city',
            'postal_code',
            'notes',

            'bipoc',
            'lgbtq',
            'has_disability',
            'immigrant_or_refugee',
            'housing_issues',
            'sex_worker',
            'single_parent',

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

            'on_behalf_of',
            'recipient_notified',
            'requester_name',
            'requester_email',
            'requester_phone_number',

            'accept_terms',
        ]
