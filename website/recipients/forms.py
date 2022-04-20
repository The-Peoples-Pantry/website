from textwrap import dedent
from django import forms

from .models import MealRequest, GroceryRequest


class MealRequestForm(forms.ModelForm):
    # Force the terms to be accepted in order to submit the form
    accept_terms = forms.BooleanField(required=True)

    class Meta:
        model = MealRequest
        exclude = [
            "created_at",
            "updated_at",
            "anonymized_latitude",
            "anonymized_longitude",
            "delivery_date",
            "status",
            "chef",
            "deliverer",
            "pickup_start",
            "pickup_end",
            "dropoff_start",
            "dropoff_end",
            "meal",
        ]


class GroceryRequestForm(forms.ModelForm):
    # Force the terms to be accepted in order to submit the form
    accept_terms = forms.BooleanField(required=True)
    can_meet_for_delivery = forms.BooleanField(
        label="Able to meet delivery driver",
        help_text="Are you (or someone in your household) able to receive the box on the delivery date assigned for your area?",
        required=True,
    )

    class Meta:
        model = GroceryRequest
        exclude = [
            "created_at",
            "updated_at",
            "anonymized_latitude",
            "anonymized_longitude",
            "delivery_date",
            "status",
        ]
