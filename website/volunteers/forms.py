from django import forms
from django.forms import BaseModelFormSet, modelformset_factory
from recipients.models import MealRequest, Delivery


class DateInput(forms.DateInput):
    input_type = 'date'


class ChefSignupForm(forms.ModelForm):
    class Meta:
        model = MealRequest
        fields = ['delivery_date']



MealFormSet = modelformset_factory(MealRequest,
        fields=('delivery_date', 'name', 'address_1', 'can_receive_texts', 'id'),
        widgets={'delivery_date': DateInput()}, extra=0)