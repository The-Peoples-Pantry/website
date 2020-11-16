from textwrap import dedent
from django.core.mail import send_mail
from django.views.generic.edit import FormView
from django.shortcuts import render
from django.urls import reverse_lazy
from .forms import MealRequestForm


def index(request):
    return render(request, 'recipients/index.html')


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
        instance = form.save()
        self.send_confirmation_email(instance)
        return super().form_valid(form)


def success(request):
    return render(request, 'recipients/success.html')
