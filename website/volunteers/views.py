from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.views.generic import ListView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django.http import HttpResponse

from recipients.models import MealRequest, Delivery

from .tables import MealRequestTable
from .filters import MealRequestFilter
from .forms import MealFormSet, ChefSignupForm


def delivery_success(request):
    return render(request, 'volunteers/delivery_success.html')


def chef_success(request):
    return render(request, 'volunteers/chef_success.html')


class IndexView(PermissionRequiredMixin, LoginRequiredMixin, SingleTableMixin, FilterView):
    model = MealRequest
    table_class = MealRequestTable
    filterset_class = MealRequestFilter
    template_name = "volunteers/index.html"
    permission_required = 'recipients.view_mealrequest'

    def anonymized_coordinates(self):
        instances = self.filterset.qs
        return {
            instance.id: [instance.anonymized_latitude, instance.anonymized_longitude, instance.id]
            for instance in instances
        }

    def google_maps_api_key(self):
        return settings.GOOGLE_MAPS_API_KEY





# THIS IS THE PROBLEM

class ChefSignupView(LoginRequiredMixin, FormView):
    model = MealRequest
    template_name = "volunteers/chef_signup.html"
    form_class = ChefSignupForm
    success_url = reverse_lazy('volunteers:chef_signup')
    meals = MealRequest.objects.filter(delivery_date__isnull=True)

    def get_context_data(self, **kwargs):
        context = super(ChefSignupView, self).get_context_data(**kwargs)
        context['formset'] = MealFormSet(queryset=self.meals)
        return context

    # Has delivery date values
    # def post(self, request, *args, **kwargs):
    #     print(request.POST)
    #     return HttpResponse("Hit POST")


    # Does not have delivery date values
    def form_valid(self, formset):
        print(formset.cleaned_data)
        # formset.save(commit=False)
        super().form_valid(formset)
        return HttpResponse("Testing")





class ChefIndexView(LoginRequiredMixin, ListView):
    model = MealRequest
    template_name = "volunteers/chef_list.html"


class DeliverySignupView(LoginRequiredMixin, FormView):
    model = Delivery
    template_name = "volunteers/delivery_signup.html"
    form_class = ChefSignupForm
    success_url = reverse_lazy('volunteers:delivery_success')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class DeliveryIndexView(LoginRequiredMixin, ListView):
    model = Delivery
    template_name = "volunteers/delivery_list.html"
