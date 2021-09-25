from textwrap import dedent
from django import forms

from .models import MealRequest, GroceryRequest


class MealRequestForm(forms.ModelForm):
    # Force the terms to be accepted in order to submit the form
    accept_terms = forms.BooleanField(required=True)

    terms_of_service_text = dedent(
        """
        I acknowledge that The People's Pantry IS NOT RESPONSIBLE FOR ANY ISSUES I MAY HAVE WITH THE FOOD THAT HAS BEEN DELIVERED TO ME. This may include, but is not limited to, allergies, food outside of dietary preferences or restrictions, or digestive tract issues caused by consuming the food. I understand that The People's Pantry will not knowingly provide me with food to which I have an allergy, is outside of my dietary restrictions, or foods that are otherwise unsafe to eat, but is not liable for any issues that may occur.

        I acknowledge that The People's Pantry IS NOT RESPONSIBLE FOR THE PRESERVATION OR PREPARATION OF ANY FOOD ONCE IT HAS BEEN DELIVERED TO ME. It is my sole responsibility to ensure that food is stored and cooked safely and that pre-cooked meals are reheated to safe temperatures.

        I acknowledge that The People's Pantry IS NOT RESPONSIBLE FOR ANY ISSUES I MAY HAVE DURING THE DELIVERY PROCESS. I understand that The People's Pantry screens all volunteers and that volunteers are to adhere to the safe delivery guidelines of The People's Pantry, but The People's Pantry is not liable for any issues caused by the volunteer. This includes, but is not limited to, delayed delivery, inappropriate behaviour, damage to property, etc. I understand that if an issue pertaining to the delivery process arises, I may contact The People's Pantry to report the volunteer, but in the event that any illegal activity occurs, it is my responsibility to contact law enforcement.

        I acknowledge that I AM NOT TO CONTACT THE DELIVERY VOLUNTEER OUTSIDE OF THE CONTEXT OF THE DELIVERY. I am not to disclose their name, phone number, or any other personal information to others.

        I understand that meals are delivered by contact-free dropoff and that if I make alternative arrangements with the deliverer that I am required to wear a mask and follow appropriate social distancing guidelines during the delivery.

        I understand that IF I DO NOT CONFIRM READINESS TO ACCEPT A DELIVERY IN A TIMELY FASHION or ACT AGGRESSIVELY AGAINST A VOLUNTEER, MY DELIVERY WILL NOT BE SCHEDULED.
    """
    )

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

    terms_of_service_text = dedent(
        """
        I acknowledge that MY NAME, EMAIL ADDRESS, PHONE NUMBER, ADDRESS, AND DELIVERY DETAILS WILL BE SHARED WITH FOODSHARE to set up my delivery.

        I acknowledge that The People's Pantry and FoodShare ARE NOT RESPONSIBLE FOR ANY ISSUES I MAY HAVE WITH THE FOOD THAT HAS BEEN DELIVERED TO ME. This may include, but is not limited to, allergies, food outside of dietary preferences or restrictions, or digestive tract issues caused by consuming the food. I understand that The People's Pantry and FoodShare are unable to assemble the produce boxes to suit my food allergies and sensitivities and dietary preferences and restrictions. The People’s Pantry will try to make sure I feel comfortable with the produce I receive, but is not liable for any issues that may occur.

        I acknowledge that The People's Pantry and FoodShare ARE NOT RESPONSIBLE FOR THE PRESERVATION OR PREPARATION OF ANY FOOD ONCE IT HAS BEEN DELIVERED TO ME. It is my sole responsibility to ensure that food is stored and cooked safely and that pre-cooked meals are reheated to safe temperatures.

        I acknowledge that The People's Pantry and FoodShare ARE NOT RESPONSIBLE FOR ANY ISSUES I MAY HAVE DURING THE DELIVERY PROCESS. This includes, but is not limited to, delayed delivery, inappropriate behaviour, damage to property, etc. I understand that if an issue pertaining to the delivery process arises, I may contact The People's Pantry to report the issue, but in the event that any illegal activity occurs, it is my responsibility to contact law enforcement.

        I acknowledge that I AM NOT TO CONTACT THE DELIVERY PERSON OUTSIDE OF THE CONTEXT OF THE DELIVERY. I am not to disclose their name, phone number, or any other personal information to others.

        I understand that IF I DO NOT CONFIRM READINESS TO ACCEPT A DELIVERY IN A TIMELY FASHION or ACT AGGRESSIVELY AGAINST A VOLUNTEER, MY DELIVERY WILL NOT BE SCHEDULED.
    """
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
