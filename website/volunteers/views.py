import logging
from django.forms import ValidationError
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView, UpdateView
from django.views.generic import ListView, TemplateView
from django_filters.views import FilterView

from core.models import has_group
from recipients.models import MealRequest, MealDelivery, Status, SendNotificationException
from public.views import GroupView
from website.maps import distance
from .forms import MealDeliverySignupForm, ChefSignupForm, ChefApplyForm, DeliveryApplyForm
from .models import VolunteerApplication, VolunteerRoles, Volunteer
from .filters import ChefSignupFilter, MealDeliverySignupFilter


logger = logging.getLogger(__name__)


def delivery_success(request):
    return render(request, 'volunteers/delivery_success.html')


class ChefSignupView(LoginRequiredMixin, GroupView, FormView, FilterView):
    """View for chefs to sign up to cook meal requests"""
    template_name = "volunteers/chef_signup.html"
    form_class = ChefSignupForm
    permission_group = 'Chefs'
    permission_group_redirect_url = reverse_lazy('volunteers:chef_application')
    filterset_class = ChefSignupFilter
    queryset = MealRequest.objects.filter(delivery__isnull=True).order_by('created_at')

    @property
    def success_url(self):
        """Redirect to the same page with same query params to keep the filters"""
        return self.request.get_full_path()

    def can_deliver(self, user):
        return has_group(user, 'Deliverers')

    def get_context_data(self, **kwargs):
        context = super(ChefSignupView, self).get_context_data(**kwargs)

        context["object_contexts"] = [
            {
                "meal": meal_request,
                "form": ChefSignupForm(initial={'id': meal_request.id}),
                "distance": distance(meal_request.coordinates, self.request.user.volunteer.coordinates),
            }
            # self.object_list is a MealRequest queryset pre-filtered by ChefSignupFilter
            for meal_request in self.object_list
        ]

        context["can_deliver"] = self.can_deliver(self.request.user)
        return context

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Sorry, we were unable to register you for that request, someone else may have already claimed it.'
        )
        return redirect(self.success_url)

    def form_valid(self, form):
        # First fetch the associated meal request
        # It's possible that someone else has signed up for it, so handle that
        meal_request = self.get_meal_request(form)
        if meal_request is None:
            return self.form_invalid(form)

        try:
            # If the meal request is still available setup the delivery
            self.create_delivery(form, meal_request)
        except ValidationError as error:
            messages.error(self.request, error.messages[0])
            return redirect(self.success_url)

        messages.success(self.request, 'Successfully signed up!')
        return super().form_valid(form)

    def get_meal_request(self, form):
        try:
            return self.queryset.get(id=form.cleaned_data['id'])
        except MealRequest.DoesNotExist:
            return None

    def create_delivery(self, form, meal_request):
        deliverer = self.request.user if form.cleaned_data['can_deliver'] else None
        delivery = MealDelivery.objects.create(
            request=meal_request,
            deliverer=deliverer,
            chef=self.request.user,
            status=Status.CHEF_ASSIGNED,
            date=form.cleaned_data['delivery_date'],
            pickup_start=form.cleaned_data['pickup_start'],
            pickup_end=form.cleaned_data['pickup_end'],
            dropoff_start=form.cleaned_data.get('dropoff_start'),
            dropoff_end=form.cleaned_data.get('dropoff_end'),
        )

        try:
            delivery.send_recipient_meal_notification()
        except SendNotificationException:
            logger.warn("Skipped sending meal notification for Meal Request %d to %s", meal_request.id, meal_request.phone_number)


class TaskIndexView(LoginRequiredMixin, GroupView, ListView):
    model = MealDelivery
    context_object_name = "deliveries"
    queryset = MealDelivery.objects.exclude(status=Status.DELIVERED).order_by('date')


class ChefIndexView(TaskIndexView):
    """View for chefs to see the meals they've signed up to cook"""
    template_name = "volunteers/chef_list.html"
    permission_group = 'Chefs'
    permission_group_redirect_url = reverse_lazy('volunteers:chef_application')

    def get_queryset(self):
        return self.queryset.filter(chef=self.request.user)


class MealDeliveryIndexView(TaskIndexView):
    """View for deliverers to see the meal requests they've signed up to deliver"""
    template_name = "volunteers/delivery_list.html"
    permission_group = 'Deliverers'
    permission_group_redirect_url = reverse_lazy('volunteers:delivery_application')

    def get_queryset(self):
        return self.queryset.filter(deliverer=self.request.user)

    def post(self, request):
        if request.POST['delivery_id']:
            instance = MealDelivery.objects.get(uuid=request.POST['delivery_id'])
            instance.status = Status.DELIVERED
            instance.save()
        return redirect(self.request.get_full_path())


class MealDeliverySignupView(LoginRequiredMixin, GroupView, FormView, FilterView):
    """View for deliverers to sign up to deliver meal requests"""
    template_name = "volunteers/delivery_signup.html"
    form_class = MealDeliverySignupForm
    permission_group = 'Deliverers'
    permission_group_redirect_url = reverse_lazy('volunteers:delivery_application')
    filterset_class = MealDeliverySignupFilter
    queryset = MealDelivery.objects.filter(deliverer__isnull=True,).order_by('date')

    @property
    def success_url(self):
        """Redirect to the same page with same query params to keep the filters"""
        return self.request.get_full_path()

    def get_context_data(self, alerts={}, **kwargs):
        context = super(MealDeliverySignupView, self).get_context_data(**kwargs)
        context["delivery_form_pairs"] = [
            (delivery, MealDeliverySignupForm(initial={
                'id': delivery.id,
                'pickup_start': delivery.pickup_start,
                'pickup_end': delivery.pickup_end
            }))
            for delivery in self.object_list
        ]
        return context

    def form_invalid(self, form):
        message = 'Sorry, we were unable to sign you for that delivery, someone else may have already claimed it.'

        if form.non_field_errors():
            message = form.non_field_errors()

        messages.error(self.request, message)
        return redirect(self.success_url)

    def form_valid(self, form):
        # First fetch the associated delivery
        delivery = self.get_delivery_request(form)

        # It's possible that someone else has signed up for it, so handle that
        if delivery is None:
            return self.form_invalid(form)

        self.update_delivery(form, delivery)

        messages.success(self.request, 'Successfully signed up!')
        return super().form_valid(form)

    def get_delivery_request(self, form):
        try:
            return self.queryset.get(id=form.cleaned_data['id'])
        except MealDelivery.DoesNotExist:
            return None

    def update_delivery(self, form, delivery):
        delivery.dropoff_start = form.cleaned_data['dropoff_start']
        delivery.dropoff_end = form.cleaned_data['dropoff_end']
        delivery.deliverer = self.request.user
        delivery.status = Status.DRIVER_ASSIGNED
        delivery.save()


class DeliveryApplicationView(LoginRequiredMixin, FormView, UpdateView):
    form_class = DeliveryApplyForm
    template_name = "volunteers/delivery_application.html"
    success_url = reverse_lazy('volunteers:delivery_application_received')

    def get_object(self):
        return Volunteer.objects.get(user=self.request.user)

    def get(self, request, *args, **kwargs):
        if VolunteerApplication.has_applied(self.request.user, VolunteerRoles.DELIVERERS):
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        application = VolunteerApplication.objects.create(user=self.request.user, role=VolunteerRoles.DELIVERERS)
        application.send_confirmation_email()
        return super().form_valid(form)


class DeliveryApplicationReceivedView(LoginRequiredMixin, TemplateView):
    template_name = "volunteers/delivery_application_received.html"


class ChefApplicationView(LoginRequiredMixin, FormView, UpdateView):
    form_class = ChefApplyForm
    template_name = "volunteers/chef_application.html"
    success_url = reverse_lazy('volunteers:chef_application_received')

    def get_object(self):
        return Volunteer.objects.get(user=self.request.user)

    def get(self, request, *args, **kwargs):
        if VolunteerApplication.has_applied(self.request.user, VolunteerRoles.CHEFS):
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        application = VolunteerApplication.objects.create(user=self.request.user, role=VolunteerRoles.CHEFS)
        application.send_confirmation_email()
        return super().form_valid(form)


class ChefApplicationReceivedView(LoginRequiredMixin, TemplateView):
    template_name = "volunteers/chef_application_received.html"


class VolunteerResourcesView(LoginRequiredMixin, TemplateView):
    template_name = "volunteers/volunteer_centre.html"
