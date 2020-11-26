import datetime
from django import forms
from recipients.models import Delivery


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


class AcceptTermsForm(forms.Form):
    accept_terms = forms.BooleanField(label="I accept the terms", required=True)


class ChefSignupForm(forms.Form):
    uuid = forms.UUIDField()
    delivery_date = forms.DateField(widget=FutureDateInput)
    start_time = TimeField(initial='09:00')
    end_time = TimeField(initial='21:00')
    container_needed = forms.BooleanField(required=False)


class DeliverySignupForm(forms.ModelForm):
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
        super(DeliverySignupForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].initial = '09:00'
        self.fields['end_time'].initial = '21:00'

    class Meta:
        model = Delivery
        fields = [
            'request',
            'uuid',
            'pickup_start',
            'pickup_end',
        ]
        widgets = {'uuid': forms.HiddenInput()}