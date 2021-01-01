import logging
from ast import literal_eval
from textwrap import dedent
import datetime
from django import forms
from recipients.models import MealDelivery, GroceryDelivery
from .models import Volunteer, CookingTypes, FoodTypes, TransportationTypes, DaysOfWeek, OrganizerTeams


logger = logging.getLogger(__name__)


def future_date(**kwargs):
    now = datetime.datetime.now().date()
    return now + datetime.timedelta(**kwargs)


class FutureDateInput(forms.DateInput):
    """A date picker widget that allows picking a date range 2-7 days from now"""

    def __init__(self):
        super().__init__(attrs={
            'type': 'date',
            'min': future_date(days=2),
            'max': future_date(days=7),
        })


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


def next_day(date):
    return date + datetime.timedelta(1)


def get_start_time_display(start_time_str):
    display_str = start_time_str
    start_time = start_time_str
    try:
        start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        end_time = start_time + datetime.timedelta(hours=3)
        display_str = start_time.strftime('%B %d, %Y %-I%p') + ' - ' + end_time.strftime('%-I%p')
    except Exception:
        logger.exception("Error when converting %s to date", start_time_str)

    return (start_time, display_str)


def next_weekend(**kwargs):
    # always leave two days of buffer time
    buffer_date = datetime.date.today() + datetime.timedelta(2)
    next_friday = buffer_date + datetime.timedelta((4 - buffer_date.weekday()) % 7)
    next_sat = next_day(next_friday)
    next_sun = next_day(next_sat)
    return [(next_friday, next_friday), (next_sat, next_sat), (next_sun, next_sun)]


class MealDeliveryDateInput(forms.Select):
    def __init__(self):
        super().__init__(
            choices=next_weekend()
        )


class VolunteerApplicationForm(forms.ModelForm):
    have_ppe = forms.BooleanField(
        label="I have access to personal protective equipment such as masks, gloves",
        required=True,
    )

    days_available = forms.MultipleChoiceField(
        label="What days of the week are you available to volunteer?",
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=DaysOfWeek.choices,
    )

    policy_text = dedent("""
        I acknowledge that I have read and understood the volunteer requirements presented at the beginning of this form pertaining to health and travel restrictions. I certify that you meet all of the requirements to volunteer.

        I acknowledge that I will, to the best of my ability, only prepare foods I feel comfortable making, follow all standard safe cooking guidelines (e.g. thoroughly cooking meat, not using any expired products, storing foods at safe temperatures, etc.), be cognizant of other's food restrictions or allergies and only volunteer to cook for a family if you can comply with these restrictions, be truthful and thorough to list all ingredients where applicable.

        I acknowledge that as a volunteer, I am being entrusted with confidential information. I understand and agree to the following: I shall not, at any time during or subsequent to my volunteering for The People's Pantry, disclose or make use of confidential information or other's personal information without permission. Examples include, but are not limited to, names, addresses, and phone numbers. I will also respect the privacy of the recipients and other volunteers and will not make contact with them beyond the context of a food pick-up/delivery.

        I agree to follow the safety and security measures provided to me by The People’s Pantry, the Canadian government, and other trusted health information providers to the best of my ability while volunteering, both for myself and others. I acknowledge that I am fully responsible for my safety and security, as well as that of my personal belongings, while volunteering. I specifically waive all liabilities, claims and/or actions against all organizations, communities, and affiliates part of the The People's Pantry.
    """)

    accept_terms = forms.BooleanField(
        label="I have carefully read and understood these terms.",
        required=True
    )

    # I know this is ugly but this is the cleanest way I could find of
    # prepopulating a multiple choice field with values that are stored as a charstring
    def __init__(self, *args, **kwargs):
        super(VolunteerApplicationForm, self).__init__(*args, **kwargs)
        for field in ['days_available', 'food_types', 'cooking_prefs', 'transportation_options']:
            if getattr(self.instance, field):
                try:
                    self.initial[field] = literal_eval(getattr(self.instance, field))
                except ValueError:
                    # Handle errors when the field is set to something invalid
                    # This can happen if the value was set manually by a staff member through the admin
                    pass

    class Meta:
        model = Volunteer
        exclude = ['user']


class ChefApplyForm(VolunteerApplicationForm):
    cooking_prefs = forms.MultipleChoiceField(
        label="What do you prefer to cook/bake? Check all that apply.",
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=CookingTypes.choices,
    )
    food_types = forms.MultipleChoiceField(
        label="What kind of meals/baked goods are you able to prepare? Check all that apply.",
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=FoodTypes.choices,
    )
    have_cleaning_supplies = forms.BooleanField(
        label="I have adequate cleaning supplies (soap, disinfectant, etc.) to clean my hands and kitchen",
        required=True
    )

    class Meta(VolunteerApplicationForm.Meta):
        exclude = [
            'transportation_options',
            'pickup_locations',
            'dropoff_locations',
            'user',
            'email',
            'pronouns',
            'training_complete',
            'organizer_teams',
        ]


class DeliveryApplyForm(VolunteerApplicationForm):
    transportation_options = forms.MultipleChoiceField(
        label="What means of transportation do you have access to for deliveries? Check all that apply.",
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=TransportationTypes.choices,
    )

    class Meta(VolunteerApplicationForm.Meta):
        model = Volunteer
        exclude = [
            'cooking_prefs',
            'food_types',
            'have_cleaning_supplies',
            'baking_volume',
            'user',
            'email',
            'pronouns',
            'training_complete',
            'organizer_teams',
        ]


class OrganizerApplyForm(VolunteerApplicationForm):
    confirm_minimum_commitment = forms.BooleanField(
        label="I can commit to the two-month minimum volunteer commitment",
        required=True,
    )
    organizer_teams = forms.MultipleChoiceField(
        label="Which teams would you be interested in joining?",
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=OrganizerTeams.choices,
    )

    policy_text = dedent("""
        I acknowledge that as a volunteer, I am being entrusted with confidential information. I understand and agree to the following: I shall not, at any time during or subsequent to my volunteering for The People's Pantry, disclose or make use of confidential information or other's personal information without permission. Examples include, but are not limited to, names, addresses, and phone numbers. I will also respect the privacy of the recipients and other volunteers and will not make contact with them beyond the context of a food pick-up/delivery.

        I agree to follow the safety and security measures provided to me by The People’s Pantry, the Canadian government, and other trusted health information providers to the best of my ability while volunteering, both for myself and others. I acknowledge that I am fully responsible for my safety and security, as well as that of my personal belongings while volunteering. I specifically waive all liabilities, claims and/or actions against all organizations, communities, and affiliates part of The People's Pantry.
    """)

    class Meta(VolunteerApplicationForm.Meta):
        model = Volunteer
        exclude = [
            'transportation_options',
            'pickup_locations',
            'dropoff_locations',
            'cooking_prefs',
            'food_types',
            'have_cleaning_supplies',
            'baking_volume',
            'user',
            'email',
            'pronouns',
            'training_complete'
        ]


class ChefSignupForm(forms.Form):
    id = forms.IntegerField()
    delivery_date = forms.DateField(widget=MealDeliveryDateInput)
    pickup_start = TimeField(initial='12:00')
    pickup_end = TimeField(initial='17:00')
    dropoff_start = TimeField(initial='18:00', required=False)
    dropoff_end = TimeField(initial='20:00', required=False)
    can_deliver = forms.BooleanField(required=False)

    # If the chef hasn't opted to deliver it, remove the dropoff timerange
    def clean(self):
        cleaned_data = super().clean()
        can_deliver = cleaned_data['can_deliver']
        if not can_deliver:
            cleaned_data.pop('dropoff_start')
            cleaned_data.pop('dropoff_end')
        return cleaned_data


class GroceryDeliverySignupForm(forms.ModelForm):
    id = forms.IntegerField()
    availability = forms.DateTimeField(widget=forms.RadioSelect, label='Dropoff timerange')

    def __init__(self, *args, **kwargs):
        super(GroceryDeliverySignupForm, self).__init__(*args, **kwargs)
        initial = kwargs.pop('initial')
        if 'id' in initial:
            request = GroceryDelivery.objects.get(id=initial['id']).request
            self.fields['availability'].widget.choices = [
                get_start_time_display(start_time)
                for start_time in literal_eval(getattr(request, 'availability'))
            ]

    class Meta:
        model = GroceryDelivery
        fields = ['id', 'availability']


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
