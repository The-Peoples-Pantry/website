from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.views.generic import ListView, TemplateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from django.contrib.auth.models import User
from recipients.models import MealRequest, Delivery, Status

from .tables import MealRequestTable
from .filters import MealRequestFilter
from .forms import DeliverySignupForm, ChefSignupForm, AcceptTermsForm
from .models import VolunteerApplication, VolunteerRoles


def delivery_success(request):
    return render(request, 'volunteers/delivery_success.html')


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


class DeliveryApplicationView(LoginRequiredMixin, FormView):
    form_class = AcceptTermsForm
    template_name = "volunteers/delivery_application.html"
    success_url = reverse_lazy('volunteers:delivery_application_received')

    def get(self, request, *args, **kwargs):
        has_applied = VolunteerApplication.objects.filter(
            user=self.request.user,
            role=VolunteerRoles.DELIVERERS,
        ).exists()
        if has_applied:
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        VolunteerApplication.objects.create(
            user=self.request.user,
            role=VolunteerRoles.DELIVERERS,
        )
        return super().form_valid(form)


class DeliveryApplicationReceivedView(LoginRequiredMixin, TemplateView):
    template_name = "volunteers/delivery_application_received.html"


class DeliverySignupView(LoginRequiredMixin, FormView):
    model = Delivery
    template_name = "volunteers/delivery_signup.html"
    form_class = DeliverySignupForm
    success_url = reverse_lazy('volunteers:delivery_success')


class ChefApplicationView(LoginRequiredMixin, FormView):
    form_class = AcceptTermsForm
    template_name = "volunteers/chef_application.html"
    success_url = reverse_lazy('volunteers:chef_application_received')

    def get(self, request, *args, **kwargs):
        has_applied = VolunteerApplication.objects.filter(
            user=self.request.user,
            role=VolunteerRoles.CHEFS,
        ).exists()
        if has_applied:
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        VolunteerApplication.objects.create(
            user=self.request.user,
            role=VolunteerRoles.CHEFS,
        )
        return super().form_valid(form)


class ChefApplicationReceivedView(LoginRequiredMixin, TemplateView):
    template_name = "volunteers/chef_application_received.html"


class DeliveryIndexView(LoginRequiredMixin, ListView):
    model = Delivery
    template_name = "volunteers/delivery_list.html"


class DeliverySignupView(LoginRequiredMixin, FormView):
    model = Delivery
    template_name = "volunteers/delivery_signup.html"
    form_class = DeliverySignupForm
    success_url = reverse_lazy('volunteers:delivery_success')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)