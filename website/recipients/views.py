from textwrap import dedent
from django.core.mail import send_mail
from django.views.generic.edit import FormView
from django.views.generic import DetailView
from django.shortcuts import render
from django.urls import reverse_lazy
from django_tables2 import SingleTableMixin
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import MealRequestForm
from .models import MealRequest
from website.maps import geocode_anonymized


def index(request):
    return render(request, 'recipients/index.html')


def success(request):
    return render(request, 'recipients/success.html')


class MealRequestView(FormView):
    template_name = 'recipients/new.html'
    form_class = MealRequestForm
    success_url = reverse_lazy('recipients:success')

    def send_confirmation_email(self, instance):
        send_mail(
            "Confirming your The People's Pantry request",
            dedent(f"""
                Hi {instance.name},
                Just confirming that we received your meal request for The People's Pantry.
                Your request ID is {instance.uuid}
            """),
            None,  # From email (by setting None, it will use DEFAULT_FROM_EMAIL)
            [instance.email]
        )

    def form_valid(self, form):
        instance = form.save(commit=False)
        self.send_confirmation_email(instance)

        entire_address = ' '.join([
            instance.address_1,
            instance.address_2,
            instance.city,
            instance.postal_code,
        ])
        instance.anonymized_latitude, instance.anonymized_longitude = geocode_anonymized(entire_address)
        instance.save()

        return super().form_valid(form)


class MealRequestDetail(LoginRequiredMixin, DetailView):
    model = MealRequest
    template_name = "recipients/meal_detail.html"
