from django.views.generic.edit import FormView
from django.views.generic import DetailView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import MealRequestForm, GroceryRequestForm
from .models import MealRequest


def index(request):
    return render(request, 'recipients/index.html')


def success(request):
    return render(request, 'recipients/success.html')


class HelpRequestView(FormView):
    success_url = reverse_lazy('recipients:success')

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.send_confirmation_email()
        return super().form_valid(form)


class MealRequestView(HelpRequestView):
    template_name = 'recipients/new_meal_request.html'
    form_class = MealRequestForm


class GroceryRequestView(HelpRequestView):
    template_name = 'recipients/new_grocery_request.html'
    form_class = GroceryRequestForm


class MealRequestDetail(LoginRequiredMixin, DetailView):
    model = MealRequest
    template_name = "recipients/meal_detail.html"
