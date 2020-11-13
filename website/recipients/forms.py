from django import forms
from .models import MealRequest, Days, TimePeriods


class TelephoneInput(forms.TextInput):
    input_type = 'tel'

    def __init__(self, attrs=None):
        attrs = {} if attrs is None else attrs
        super().__init__(attrs={
            'pattern': r'\(?[0-9]{3}\)?[- ]?[0-9]{3}[- ]?[0-9]{4}',
            'title': 'Telephone input in the form xxx-xxx-xxxx',
            **attrs,
        })


class MealRequestForm(forms.ModelForm):
    # Field overrides
    available_days = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=Days.choices,
    )
    available_time_periods = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=TimePeriods.choices,
    )

    class Meta:
        model = MealRequest
        exclude = ['uuid', 'created_at', 'updated_at', 'anonymized_latitude', 'anonymized_longitude']

        widgets = {
            'phone_number': TelephoneInput(),
            'requester_phone_number': TelephoneInput(),
        }
