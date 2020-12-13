import datetime
from textwrap import dedent
from django import forms
from .models import MealRequest, GroceryRequest, Vegetables, Fruits, Grains, Condiments, Protein, Dairy
from django.conf import settings


def day_to_datetime(day, oclock):
    return datetime.datetime.combine(day, datetime.time(oclock))


def get_grocery_delivery_days():
    grocery_shifts = []
    for day in settings.GROCERY_DELIVERY_DAYS:
        grocery_shifts.append((day_to_datetime(day, 12), day.strftime("%B %d, %Y") + ' 12-3pm'))
        grocery_shifts.append((day_to_datetime(day, 15), day.strftime("%B %d, %Y") + ' 3-6m'))

    return grocery_shifts


class TelephoneInput(forms.TextInput):
    input_type = 'tel'

    def __init__(self, attrs=None):
        attrs = {} if attrs is None else attrs
        super().__init__(attrs={
            'pattern': r'\(?[0-9]{3}\)?[- ]?[0-9]{3}[- ]?[0-9]{4}',
            'title': 'Telephone input in the form xxx-xxx-xxxx',
            **attrs,
        })


class HelpRequestForm(forms.ModelForm):
    # Force the terms to be accepted in order to submit the form
    accept_terms = forms.BooleanField(required=True)
    can_meet_for_delivery = forms.BooleanField(required=True, help_text="Please confirm that you / the person requiring support will be able to meet the delivery person in the lobby or door of the residence, while wearing protective equipment such as masks?")

    terms_of_service_text = dedent("""
        I acknowledge that The People's Pantry IS NOT RESPONSIBLE FOR ANY ISSUES I MAY HAVE WITH THE FOOD THAT HAS BEEN DELIVERED TO ME. This may include, but is not limited to, allergies, food outside of dietary preferences or restrictions, or digestive tract issues caused by consuming the food. I understand that The People's Pantry will not knowingly provide me with food to which I have an allergy, is outside of my dietary restrictions, or foods that are otherwise unsafe to eat, but is not liable for any issues that may occur.

        I acknowledge that The People's Pantry IS NOT RESPONSIBLE FOR THE PRESERVATION OR PREPARATION OF ANY FOOD ONCE IT HAS BEEN DELIVERED TO ME. It is my sole responsibility to ensure that food is stored and cooked safely and that pre-cooked meals are reheated to safe temperatures.

        I acknowledge that The People's Pantry IS NOT RESPONSIBLE FOR ANY ISSUES I MAY HAVE DURING THE DELIVERY PROCESS. I understand that The People's Pantry screens all volunteers and that volunteers are to adhere to the safe delivery guidelines of The People's Pantry, but The People's Pantry is not liable for any issues caused by the volunteer. This includes, but is not limited to, delayed delivery, inappropriate behaviour, damage to property, etc. I understand that if an issue pertaining to the delivery process arises, I may contact The People's Pantry to report the volunteer, but in the event that any illegal activity occurs, it is my responsibility to contact law enforcement.

        I acknowledge that I AM NOT TO CONTACT THE DELIVERY VOLUNTEER OUTSIDE OF THE CONTEXT OF THE DELIVERY. I am not to disclose their name, phone number, or any other personal information to others.

        I understand that IF I DO NOT CONFIRM READINESS TO ACCEPT A DELIVERY IN A TIMELY FASHION or ACT AGGRESSIVELY AGAINST A VOLUNTEER, MY DELIVERY WILL NOT BE SCHEDULED.
    """)

    class Meta:
        exclude = ['uuid', 'created_at', 'updated_at', 'anonymized_latitude', 'anonymized_longitude']

        widgets = {
            'phone_number': TelephoneInput(),
            'requester_phone_number': TelephoneInput(),
            'food_allergies': forms.Textarea(attrs={'rows': 3}),
            'food_preferences': forms.Textarea(attrs={'rows': 3}),
            'delivery_details': forms.Textarea(attrs={'rows': 3}),
            'availability': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class MealRequestForm(HelpRequestForm):
    class Meta(HelpRequestForm.Meta):
        model = MealRequest


class GroceryRequestForm(HelpRequestForm):
    class Meta(HelpRequestForm.Meta):
        model = GroceryRequest

    vegetables = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=Vegetables.choices,
    )
    fruits = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=Fruits.choices,
    )
    grains = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=Grains.choices,
    )
    condiments = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=Condiments.choices,
    )
    protein = forms.ChoiceField(
        required=False,
        choices=Protein.choices,
    )
    dairy = forms.ChoiceField(
        required=False,
        choices=Dairy.choices,
    )
    availability = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=get_grocery_delivery_days,
    )
