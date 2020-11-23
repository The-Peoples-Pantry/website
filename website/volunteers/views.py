from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.views.generic import ListView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from django.contrib.auth.models import User
from recipients.models import MealRequest, Delivery, Status

from .tables import MealRequestTable
from .filters import MealRequestFilter, ChefSignupFilter
from .forms import ChefSignupForm


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


class ChefSignupView(LoginRequiredMixin, FormView):
    model = MealRequest
    template_name = "volunteers/chef_signup.html"
    form_class = ChefSignupForm
    success_url = reverse_lazy('volunteers:chef_signup')

    def get_context_data(self, alerts={}, **kwargs):
        context = super(ChefSignupView, self).get_context_data(**kwargs)

        meals = []
        for meal in MealRequest.objects.filter(delivery_date__isnull=True):
            meals.append(ChefSignupForm(instance=meal))

        context['meals'] = meals
        context['alerts'] = alerts

        return context


    def create_delivery(self, data, user):
        user_object = User.objects.get(pk=user.id)
        meal_object = MealRequest.objects.get(uuid=data['uuid'])

        try:
            instance = Delivery.objects.get(request=meal_object)
        except Delivery.DoesNotExist as exception:
            instance = Delivery.objects.create(
                request=meal_object,
                chef=user_object,
                status=Status.CHEF_ASSIGNED,
                pickup_start=data['start_time'],
                pickup_end=data['end_time']
            )
            instance.user = user_object
            instance.save()


    def post(self, request):
        data = request.POST
        alerts = {'success': False, 'no_date': False}

        try:
            if data['delivery_date']:
                instance = MealRequest.objects.get(uuid=data['uuid'])
                instance.delivery_date = data['delivery_date']
                self.create_delivery(data, request.user)

                instance.save()
                alerts['success'] = True
            else:
                alerts['no_date'] = True
        except:
            print("Exception raised while saving a sign-up request")

        return render(request, self.template_name, self.get_context_data(alerts))


class ChefIndexView(LoginRequiredMixin, ListView):
    model = Delivery
    template_name = "volunteers/chef_list.html"
    context_object_name = "deliveries"

    def get_queryset(self):
        user = self.request.user
        return Delivery.objects.filter(chef=User.objects.get(pk=user.id))


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
