import datetime
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.views.generic import ListView, TemplateView
from django.contrib.auth.models import User
from django_filters.views import FilterView

from recipients.models import MealRequest, Delivery, Status
from public.views import GroupView
from .forms import DeliverySignupForm, ChefSignupForm, AcceptTermsForm
from .models import VolunteerApplication, VolunteerRoles
from .filters import ChefSignupFilter, DeliverySignupFilter


def delivery_success(request):
    return render(request, 'volunteers/delivery_success.html')


class ChefSignupView(LoginRequiredMixin, GroupView, FormView, FilterView):
    """View for chefs to sign up to cook meal requests"""
    template_name = "volunteers/chef_signup.html"
    form_class = ChefSignupForm
    success_url = reverse_lazy('volunteers:chef_signup')
    permission_group = 'Chefs'
    filterset_class = ChefSignupFilter

    def get_context_data(self, **kwargs):
        context = super(ChefSignupView, self).get_context_data(**kwargs)
        context["meals"] = [
            {
                'meal': meal,
                'form': ChefSignupForm(initial={'uuid': meal.uuid}),
            }
            # self.object_list is a MealRequest queryset pre-filtered by ChefSignupFilter
            for meal in self.object_list
        ]
        return context

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid selection')
        return super().form_invalid(form)

    def form_valid(self, form):
        meal_request = self.get_meal_request(form)
        self.update_meal_request(form, meal_request)
        self.create_delivery(form, meal_request)
        if form.cleaned_data['container_needed']:
            self.create_container_delivery(form, meal_request)
        messages.success(self.request, 'Successfully signed up!')
        return super().form_valid(form)

    def get_meal_request(self, form):
        return MealRequest.objects.get(uuid=form.cleaned_data['uuid'])

    def update_meal_request(self, form, meal_request):
        meal_request.delivery_date = form.cleaned_data['delivery_date']
        meal_request.save()

    def create_delivery(self, form, meal_request):
        Delivery.objects.create(
            request=meal_request,
            chef=self.request.user,
            status=Status.CHEF_ASSIGNED,
            pickup_start=form.cleaned_data['start_time'],
            pickup_end=form.cleaned_data['end_time']
        )

    def create_container_delivery(self, form, meal_request):
        Delivery.objects.create(
            request=meal_request,
            chef=self.request.user,
            status=Status.CHEF_ASSIGNED,
            pickup_start=form.cleaned_data['start_time'],
            pickup_end=form.cleaned_data['end_time'],
            container_delivery=True
        )


class ChefIndexView(LoginRequiredMixin, GroupView, ListView):
    """View for chefs to see the meals they've signed up to cook"""
    model = Delivery
    template_name = "volunteers/chef_list.html"
    context_object_name = "deliveries"
    permission_group = 'Chefs'

    def get_queryset(self):
        user = self.request.user
        return Delivery.objects.filter(
            chef=User.objects.get(pk=user.id)
        ).exclude(
            status=Status.DELIVERED
        ).order_by('request__delivery_date')



class DeliveryIndexView(LoginRequiredMixin, GroupView, ListView):
    model = Delivery
    template_name = "volunteers/delivery_list.html"
    context_object_name = "deliveries"
    permission_group = 'Deliverers'

    def get_queryset(self):
        user = self.request.user
        return Delivery.objects.filter(
            chef=User.objects.get(pk=user.id)
        ).exclude(
            status=Status.DELIVERED
        ).order_by('request__delivery_date')


class DeliverySignupView(LoginRequiredMixin, GroupView, FormView, FilterView):
    model = Delivery
    template_name = "volunteers/delivery_signup.html"
    form_class = DeliverySignupForm
    success_url = reverse_lazy('volunteers:delivery_signup')
    permission_group = 'Deliverers'
    filterset_class = DeliverySignupFilter

    def get_context_data(self, alerts={}, **kwargs):
        context = super(DeliverySignupView, self).get_context_data(**kwargs)

        today = datetime.datetime.now().date()
        deliveries = []
        for delivery in context['delivery_list'].filter(
            deliverer__isnull=True,
            request__delivery_date__range=[today,today + datetime.timedelta(days=7)]
        ).order_by('request__delivery_date'):
            delivery_date = delivery.request.delivery_date

            # If this is a container delivery, it needs to happen two days before the actual meal
            if delivery.container_delivery:
                delivery.request.delivery_date = delivery_date - datetime.timedelta(days=2)

            deliveries.append({
                'request': delivery.request,
                'delivery': delivery,
                'form': DeliverySignupForm(instance=delivery)
            })

        context['deliveries'] = deliveries
        context['alerts'] = alerts
        return context

    def post(self, request):
        data = request.POST
        alerts = {'success': False, 'errors': None}

        try:
            instance = Delivery.objects.get(uuid=data['uuid'])
            instance.dropoff_start = data['start_time']
            instance.dropoff_end = data['end_time']
            instance.deliverer = User.objects.get(pk=request.user.id)
            instance.status = Status.SCHEDULED
            instance.save()
            alerts['success'] = True

        except Exception as e:
            print("Exception raised while saving a delivery sign-up: %s" % e)

        return render(request, self.template_name, self.get_context_data(alerts))


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