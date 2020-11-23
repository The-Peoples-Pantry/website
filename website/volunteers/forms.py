from django import forms
from recipients.models import MealRequest, Delivery

class DateInput(forms.DateInput):
    input_type = 'date'


class TimeInput(forms.TimeInput):
    input_type="time"
    input_format='%H:%M'


class AcceptTermsForm(forms.Form):
    accept_terms = forms.BooleanField(label="I accept the terms", required=True)


class ChefSignupForm(forms.ModelForm):
    start_time = forms.TimeField(
        input_formats='%H:%M %p',
        widget=forms.TimeInput(
            format='%H:%M', attrs={'type': 'time'}
        )
    )
    end_time = forms.TimeField(
        input_formats='%H:%M %p',
        widget=forms.TimeInput(
            format='%H:%M',
            attrs={'type': 'time'}
        )
    )


    def __init__(self, *args, **kwargs):
        super(ChefSignupForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].initial = '09:00'
        self.fields['end_time'].initial = '21:00'


    class Meta:
        model = MealRequest
        fields = [
            'delivery_date',
            'uuid',
            'num_adults',
            'num_children',
            'vegan',
            'vegetarian',
            'dairy_free',
            'gluten_free',
            'halal',
            'low_carb',
            'food_preferences',
            'food_allergies',
            'start_time',
            'end_time'
        ]
        widgets= {
            'delivery_date': DateInput(),
            'uuid': forms.HiddenInput()
        }


class DeliverySignupForm(forms.ModelForm):
    accept_terms = forms.BooleanField(required=True)
    class Meta:
        model = Delivery
        fields = ['request']