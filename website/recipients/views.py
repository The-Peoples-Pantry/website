from textwrap import dedent
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib import messages

from .forms import MealRequestForm, GroceryRequestForm
from .models import MealRequest, GroceryRequest


class RequestIndexView(TemplateView):
    template_name = "recipients/index.html"


class RequestSuccessView(TemplateView):
    template_name = "recipients/success.html"


class MealRequestView(FormView):
    template_name = "recipients/new_meal_request.html"
    success_url = reverse_lazy("recipients:success")
    form_class = MealRequestForm
    initial = {
        "num_children": 0,
    }

    def dispatch(self, request):
        if MealRequest.requests_paused():
            return render(request, "recipients/meal_paused.html")
        return super().dispatch(request)

    def get_duplicate(self, form):
        phone = form.cleaned_data["phone_number"]
        return MealRequest.has_open_request(phone)

    def form_valid(self, form):
        if self.get_duplicate(form):
            messages.warning(
                self.request,
                dedent(
                    """
                We're sorry, it looks like we currently have an unfulfilled request on file for you already.
                Please give us some time to fulfill that request first before submitting another.
            """
                ),
            )
            return super().form_invalid(form)

        instance = form.save()
        instance.send_confirmation_email()
        return super().form_valid(form)


class GroceryRequestView(FormView):
    template_name = "recipients/new_grocery_request.html"
    success_url = reverse_lazy("recipients:success")
    form_class = GroceryRequestForm
    initial = {
        "num_children": 0,
    }

    def dispatch(self, request):
        if GroceryRequest.requests_paused():
            return render(request, "recipients/grocery_paused.html")
        return super().dispatch(request)

    def get_duplicate(self, form):
        phone = form.cleaned_data["phone_number"]
        return GroceryRequest.has_open_request(phone)

    def form_valid(self, form):
        if self.get_duplicate(form):
            messages.warning(
                self.request,
                dedent(
                    """
                We're sorry, it looks like we currently have an unfulfilled request on file for you already.
                Please give us some time to fulfill that request first before submitting another.
            """
                ),
            )
            return super().form_invalid(form)

        instance = form.save()
        instance.send_confirmation_email()
        return super().form_valid(form)
