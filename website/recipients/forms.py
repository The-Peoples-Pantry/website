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
    accept_terms = forms.BooleanField(required=True)

    class Meta:
        model = MealRequest
        exclude = ['uuid', 'created_at', 'updated_at']

        widgets = {
            'phone_number': TelephoneInput(),
            'requester_phone_number': TelephoneInput(),
            'food_allergies': forms.Textarea(attrs={'rows': 3}),
            'food_preferences': forms.Textarea(attrs={'rows': 3}),
            'delivery_details': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
