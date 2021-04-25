import logging
from textwrap import dedent
import datetime
from django import forms
from django.core.exceptions import ValidationError
from recipients.models import MealRequest
from .models import Volunteer


logger = logging.getLogger(__name__)


class TimeInput(forms.TimeInput):
    input_type = 'time'


def time_difference(t_start, t_end):
    today = datetime.datetime.today()
    return datetime.datetime.combine(today, t_end) - datetime.datetime.combine(today, t_start)


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


class DelivererApplyForm(VolunteerApplicationForm):
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


class ChefSignupForm(forms.ModelForm):
    can_deliver = forms.BooleanField(label="I can also deliver this meal myself", required=False)
    delivery_date = forms.ChoiceField(choices=next_weekend, required=True)

    class Meta:
        model = MealRequest
        fields = [
            'delivery_date',
            'pickup_start',
            'pickup_end',
            'dropoff_start',
            'dropoff_end',
            'pickup_details',
            'meal',
            'containers',
        ]
        widgets = {
            'pickup_start': TimeInput,
            'pickup_end': TimeInput,
            'dropoff_start': TimeInput,
            'dropoff_end': TimeInput,
        }

    def clean(self):
        cleaned_data = super().clean()
        can_deliver = cleaned_data.get('can_deliver')
        pickup_start = cleaned_data.get('pickup_start')
        pickup_end = cleaned_data.get('pickup_end')
        dropoff_start = cleaned_data.get('dropoff_start')
        dropoff_end = cleaned_data.get('dropoff_end')

        if pickup_end <= pickup_start:
            self.add_error('pickup_end', ValidationError("The pickup end time must come after the pickup start time"))

        # Only try to validate the dropoff window if the chef is delivering it (setting these values themselves)
        if can_deliver:
            if dropoff_end <= dropoff_start:
                self.add_error('dropoff_end', ValidationError("The dropoff end time must come after the dropoff start time"))
            if dropoff_start < pickup_start:
                self.add_error('dropoff_start', ValidationError("The dropoff start time cannot come before the pickup start time"))
            if time_difference(dropoff_start, dropoff_end) > datetime.timedelta(hours=2):
                self.add_error('dropoff_end', ValidationError("The delivery window cannot be longer than 2 hours"))


class ChefTaskForm(forms.ModelForm):
    class Meta:
        model = MealRequest
        fields = ['pickup_details', 'meal']


class DelivererSignupForm(forms.ModelForm):
    class Meta:
        model = MealRequest
        fields = [
            'dropoff_start',
            'dropoff_end',
        ]
        widgets = {
            'dropoff_start': TimeInput,
            'dropoff_end': TimeInput,
        }

    def clean(self):
        cleaned_data = super().clean()
        dropoff_start = cleaned_data.get('dropoff_start')
        dropoff_end = cleaned_data.get('dropoff_end')

        if dropoff_end <= dropoff_start:
            self.add_error('dropoff_end', ValidationError("The dropoff end time must come after the dropoff start time"))
        if time_difference(dropoff_start, dropoff_end) > datetime.timedelta(hours=2):
            self.add_error('dropoff_end', ValidationError("The delivery window cannot be longer than 2 hours"))
