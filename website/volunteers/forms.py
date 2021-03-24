import logging
from textwrap import dedent
import datetime
from django import forms
from recipients.models import MealDelivery
from .models import Volunteer


logger = logging.getLogger(__name__)


class TimeField(forms.TimeField):
    """A field that renders a time picker widget"""

    def __init__(self, **kwargs):
        super().__init__(
            input_formats=['%H:%M'],
            widget=forms.TimeInput(
                format='%H:%M',
                attrs={'type': 'time'}
            ),
            **kwargs,
        )


def date_label(date):
    return date.strftime("%A %B %-d, %Y")


def next_day(date):
    return date + datetime.timedelta(1)


def next_weekend(**kwargs):
    # always leave two days of buffer time
    buffer_date = datetime.date.today() + datetime.timedelta(2)
    next_friday = buffer_date + datetime.timedelta((4 - buffer_date.weekday()) % 7)
    next_sat = next_day(next_friday)
    next_sun = next_day(next_sat)
    return [
        (next_friday, date_label(next_friday)),
        (next_sat, date_label(next_sat)),
        (next_sun, date_label(next_sun)),
    ]


class MealDeliveryDateInput(forms.Select):
    def __init__(self):
        super().__init__(
            choices=next_weekend()
        )


class VolunteerApplicationForm(forms.ModelForm):
    policy_text = dedent("""
        I acknowledge that I have read and understood the volunteer requirements presented at the beginning of this form pertaining to health and travel restrictions. I certify that you meet all of the requirements to volunteer.

        I acknowledge that I will, to the best of my ability, only prepare foods I feel comfortable making, follow all standard safe cooking guidelines (e.g. thoroughly cooking meat, not using any expired products, storing foods at safe temperatures, etc.), be cognizant of other's food restrictions or allergies and only volunteer to cook for a family if you can comply with these restrictions, be truthful and thorough to list all ingredients where applicable.

        I acknowledge that as a volunteer, I am being entrusted with confidential information. I understand and agree to the following: I shall not, at any time during or subsequent to my volunteering for The People's Pantry, disclose or make use of confidential information or other's personal information without permission. Examples include, but are not limited to, names, addresses, and phone numbers. I will also respect the privacy of the recipients and other volunteers and will not make contact with them beyond the context of a food pick-up/delivery.

        I agree to follow the safety and security measures provided to me by The People’s Pantry, the Canadian government, and other trusted health information providers to the best of my ability while volunteering, both for myself and others. I acknowledge that I am fully responsible for my safety and security, as well as that of my personal belongings, while volunteering. I specifically waive all liabilities, claims and/or actions against all organizations, communities, and affiliates part of the The People's Pantry.
    """)

    have_ppe = forms.BooleanField(
        label="I have access to personal protective equipment such as masks, gloves",
        required=True,
    )
    accept_terms = forms.BooleanField(
        label="I have carefully read and understood these terms.",
        required=True
    )

    class Meta:
        model = Volunteer
        fields = [
            'name',
            'short_name',
            'phone_number',
            'address_1',
            'address_2',
            'city',
            'postal_code',
            'days_available',
            'total_hours_available',
            'recurring_time_available',
            'have_ppe',
        ]


class ChefApplyForm(VolunteerApplicationForm):
    have_cleaning_supplies = forms.BooleanField(
        label="I have adequate cleaning supplies (soap, disinfectant, etc.) to clean my hands and kitchen",
        required=True
    )

    class Meta(VolunteerApplicationForm.Meta):
        fields = [
            *VolunteerApplicationForm.Meta.fields,
            'cooking_prefs',
            'baking_volume',
            'food_types',
            'have_cleaning_supplies',
        ]


class DeliveryApplyForm(VolunteerApplicationForm):
    class Meta(VolunteerApplicationForm.Meta):
        fields = [
            *VolunteerApplicationForm.Meta.fields,
            'transportation_options',
        ]


class OrganizerApplyForm(VolunteerApplicationForm):
    policy_text = dedent("""
        I acknowledge that as a volunteer, I am being entrusted with confidential information. I understand and agree to the following: I shall not, at any time during or subsequent to my volunteering for The People's Pantry, disclose or make use of confidential information or other's personal information without permission. Examples include, but are not limited to, names, addresses, and phone numbers. I will also respect the privacy of the recipients and other volunteers and will not make contact with them beyond the context of a food pick-up/delivery.

        I agree to follow the safety and security measures provided to me by The People’s Pantry, the Canadian government, and other trusted health information providers to the best of my ability while volunteering, both for myself and others. I acknowledge that I am fully responsible for my safety and security, as well as that of my personal belongings while volunteering. I specifically waive all liabilities, claims and/or actions against all organizations, communities, and affiliates part of The People's Pantry.
    """)

    confirm_minimum_commitment = forms.BooleanField(
        label="I can commit to the two-month minimum volunteer commitment",
        required=True,
    )

    class Meta(VolunteerApplicationForm.Meta):
        fields = [
            *VolunteerApplicationForm.Meta.fields,
            'organizer_teams',
            'confirm_minimum_commitment',
        ]


class ChefSignupForm(forms.Form):
    id = forms.IntegerField()
    delivery_date = forms.DateField(widget=MealDeliveryDateInput)
    pickup_start = TimeField(initial='12:00')
    pickup_end = TimeField(initial='17:00')
    dropoff_start = TimeField(initial='18:00', required=False)
    dropoff_end = TimeField(initial='20:00', required=False)
    can_deliver = forms.BooleanField(required=False)
    meal = forms.CharField(
        required=False,
        help_text="(Optional) Let us know what you plan on cooking!",
        widget=forms.Textarea(attrs={'rows': 3})
    )

    # If the chef hasn't opted to deliver it, remove the dropoff timerange
    def clean(self):
        cleaned_data = super().clean()
        can_deliver = cleaned_data['can_deliver']
        if not can_deliver:
            cleaned_data.pop('dropoff_start')
            cleaned_data.pop('dropoff_end')
        return cleaned_data


class MealDeliverySignupForm(forms.ModelForm):
    id = forms.IntegerField()
    dropoff_start = TimeField(initial='18:00')
    dropoff_end = TimeField(initial='20:00')

    class Meta:
        model = MealDelivery
        fields = [
            'id',
            'pickup_start',
            'pickup_end',
            'dropoff_start',
            'dropoff_end',
        ]
