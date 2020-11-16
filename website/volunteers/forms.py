from django import forms

class ChefSignupForm(forms.ModelForm):
    accept_terms = forms.BooleanField(required=True)


class DeliverySignupForm(forms.ModelForm):
    accept_terms = forms.BooleanField(required=True)