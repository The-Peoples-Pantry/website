from django import forms


class AcceptTermsForm(forms.Form):
    accept_terms = forms.BooleanField(label="I accept the terms", required=True)


class ChefSignupForm(forms.ModelForm):
    accept_terms = forms.BooleanField(required=True)


class DeliverySignupForm(forms.ModelForm):
    accept_terms = forms.BooleanField(required=True)
