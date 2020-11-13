from django.views.generic.edit import FormView
from django.shortcuts import render
from django.urls import reverse_lazy
from .forms import MealRequestForm
from website import maps


def index(request):
    return render(request, 'recipients/index.html')


class MealRequestView(FormView):
    template_name = 'recipients/new.html'
    form_class = MealRequestForm
    success_url = reverse_lazy('recipients:success')

    def form_valid(self, form):
        meal_request = form.save(commit=False)
        entire_address = ' '.join([
            meal_request.address_1,
            meal_request.address_2,
            meal_request.city,
            meal_request.postal_code,
        ])
        meal_request.anonymized_latitude, meal_request.anonymized_longitude = maps.geocode_anonymized(entire_address)
        meal_request.save()
        return super().form_valid(form)


def success(request):
    return render(request, 'recipients/success.html')
