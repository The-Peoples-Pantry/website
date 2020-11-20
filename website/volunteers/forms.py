from django import forms
from recipients.models import MealRequest, Delivery

class DateInput(forms.DateInput):
    input_type = 'date'


class ChefSignupForm(forms.ModelForm):
    start_range = forms.CharField(max_length=20, required=False)
    end_range = forms.CharField(max_length=20, required=False)

    class Meta:
        model = MealRequest
        fields = ['delivery_date', 'uuid', 'address_1', 'name']
        widgets= {'delivery_date': DateInput(), 'uuid': forms.HiddenInput()}