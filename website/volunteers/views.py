from itertools import chain
import logging
import time
from datetime import timedelta, date
from django.conf import settings
from django.forms import ValidationError
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView, UpdateView
from django.views.generic import ListView, TemplateView
from django_filters.views import FilterView
from django.db.models.query_utils import Q

from core.models import has_group
from recipients.models import MealRequest, GroceryRequest, GroceryDelivery, MealDelivery, Status, SendNotificationException
from public.views import GroupView
from website.maps import distance
from .forms import GroceryDeliverySignupForm, MealDeliverySignupForm, ChefSignupForm, ChefApplyForm, DeliveryApplyForm, OrganizerApplyForm
from .models import VolunteerApplication, VolunteerRoles, Volunteer
from .filters import ChefSignupFilter, MealDeliverySignupFilter, GroceryDeliverySignupFilter


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
    queryset = MealRequest.objects.exclude(delivery__status=Status.DELIVERED).filter(
        Q(delivery__isnull=True) | Q(delivery__chef__isnull=True)
    ).order_by('created_at')

    @property
    def success_url(self):
        """Redirect to the same page with same query params to keep the filters"""
        return self.request.get_full_path()

    def can_deliver(self, user):
        return has_group(user, 'Deliverers')

    def get_and_set_last_visited(self):
        """Retrieve the timestamp when this user last viewed this page, then set a new one"""
        session_key = 'last_visited_chef_signup'
        last_visited = self.request.session.get(session_key, 0)
        self.request.session[session_key] = time.time()
        return last_visited

    def new_since(self, timestamp):
        """Count how many of object_list are new (created) since a given timestamp"""
        return len([
            obj for obj in self.object_list
            if timestamp < obj.created_at.timestamp()
        ])

    def get_context_data(self, **kwargs):
        context = super(ChefSignupView, self).get_context_data(**kwargs)
        last_visited = self.get_and_set_last_visited()
        context["object_contexts"] = [
            {
                "meal": meal_request,
                "form": ChefSignupForm(initial={'id': meal_request.id}),
                "distance": distance(meal_request.coordinates, self.request.user.volunteer.coordinates),
            }
            # self.object_list is a MealRequest queryset pre-filtered by ChefSignupFilter
            for meal_request in self.object_list
        ]
        context["last_visited"] = last_visited
        context["new_since_last_visited"] = self.new_since(last_visited)
        context["can_deliver"] = self.can_deliver(self.request.user)
        return context

    def form_invalid(self, form):
        return redirect(self.success_url)

    def form_valid(self, form):
        # First fetch the associated meal request
        # It's possible that someone else has signed up for it, so handle that
        meal_request = self.get_meal_request(form)
        if meal_request is None:
            messages.error(
                self.request,
                'Sorry, we were unable to register you for that request, someone else may have already claimed it.'
            )
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
        if form.cleaned_data['can_deliver']:
            MealDelivery.objects.create(
                request=meal_request,
                deliverer=self.request.user,
                chef=self.request.user,
                status=Status.DRIVER_ASSIGNED,
                date=form.cleaned_data['delivery_date'],
                pickup_start=form.cleaned_data['pickup_start'],
                pickup_end=form.cleaned_data['pickup_end'],
                dropoff_start=form.cleaned_data['dropoff_start'],
                dropoff_end=form.cleaned_data['dropoff_end'],
            )
        else:
            MealDelivery.objects.create(
                request=meal_request,
                chef=self.request.user,
                status=Status.CHEF_ASSIGNED,
                date=form.cleaned_data['delivery_date'],
                pickup_start=form.cleaned_data['pickup_start'],
                pickup_end=form.cleaned_data['pickup_end'],
            )


class GroceryDeliverySignupView(LoginRequiredMixin, GroupView, FormView, FilterView):
    """View for deliverers to sign up to deliver meal requests"""
    template_name = "volunteers/delivery_signup_groceries.html"
    form_class = GroceryDeliverySignupForm
    permission_group = 'Deliverers'
    permission_group_redirect_url = reverse_lazy('volunteers:delivery_application')
    filterset_class = GroceryDeliverySignupFilter
    queryset = GroceryDelivery.objects.filter(deliverer__isnull=True)

    @property
    def success_url(self):
        """Redirect to the same page with same query params to keep the filters"""
        return self.request.get_full_path()

    def get_context_data(self, **kwargs):
        context = super(GroceryDeliverySignupView, self).get_context_data(**kwargs)

        context["grocery_delivery_form_pairs"] = [
            (grocery_delivery, GroceryDeliverySignupForm(initial={'id': grocery_delivery.id}))
            for grocery_delivery in self.object_list
        ]
        return context

    def form_invalid(self, form):
        return redirect(self.success_url)

    def form_valid(self, form):
        # First fetch the associated meal request
        # It's possible that someone else has signed up for it, so handle that
        grocery_request = self.get_grocery_request(form)

        if grocery_request is None:
            messages.error(
                self.request,
                'Sorry, we were unable to register you for that request, someone else may have already claimed it.'
            )
            return self.form_invalid(form)

        try:
            # If the grocery request is still available setup the delivery
            self.update_delivery(form, grocery_request)
        except ValidationError as error:
            messages.error(self.request, error.messages[0])
            return redirect(self.success_url)

        messages.success(self.request, 'Successfully signed up!')
        return super().form_valid(form)

    def get_grocery_request(self, form):
        try:
            return self.queryset.get(id=form.cleaned_data['id'])
        except GroceryRequest.DoesNotExist:
            return None

    def update_delivery(self, form, grocery_request):
        start_time = form.cleaned_data['availability']
        grocery_request.status = Status.DRIVER_ASSIGNED
        grocery_request.pickup_start = start_time - timedelta(hours=1)
        grocery_request.pickup_end = start_time
        grocery_request.dropoff_start = start_time
        grocery_request.dropoff_end = start_time + timedelta(hours=3)
        grocery_request.deliverer = self.request.user
        grocery_request.date = start_time.date()
        grocery_request.save()

        try:
            grocery_request.send_recipient_delivery_notification()
        except SendNotificationException:
            logger.warn("Skipped sending notification for Grocery Request %d to %s", grocery_request.id, grocery_request.phone_number)


class MealDeliverySignupView(LoginRequiredMixin, GroupView, FormView, FilterView):
    """View for deliverers to sign up to deliver meal requests"""
    template_name = "volunteers/delivery_signup_meals.html"
    form_class = MealDeliverySignupForm
    permission_group = 'Deliverers'
    permission_group_redirect_url = reverse_lazy('volunteers:delivery_application')
    filterset_class = MealDeliverySignupFilter
    queryset = MealDelivery.objects.exclude(status=Status.DELIVERED).filter(deliverer__isnull=True,).order_by('date')

    @property
    def success_url(self):
        """Redirect to the same page with same query params to keep the filters"""
        return self.request.get_full_path()

    def get_and_set_last_visited(self):
        """Retrieve the timestamp when this user last viewed this page, then set a new one"""
        session_key = 'last_visited_delivery_signup'
        last_visited = self.request.session.get(session_key, 0)
        self.request.session[session_key] = time.time()
        return last_visited

    def new_since(self, timestamp):
        """Count how many of object_list are new (created) since a given timestamp"""
        return len([
            obj for obj in self.object_list
            if timestamp < obj.created_at.timestamp()
        ])

    def get_context_data(self, alerts={}, **kwargs):
        context = super(MealDeliverySignupView, self).get_context_data(**kwargs)
        last_visited = self.get_and_set_last_visited()
        context["delivery_form_pairs"] = [
            (delivery, MealDeliverySignupForm(initial={
                'id': delivery.id,
                'pickup_start': delivery.pickup_start,
                'pickup_end': delivery.pickup_end
            }))
            for delivery in self.object_list
        ]
        context["new_since_last_visited"] = self.new_since(last_visited)
        context["last_visited"] = last_visited
        return context

    def form_invalid(self, form):
        if form.non_field_errors():
            messages.error(self.request, form.non_field_errors())
        return redirect(self.success_url)

    def form_valid(self, form):
        # First fetch the associated delivery
        delivery = self.get_delivery_request(form)

        # It's possible that someone else has signed up for it, so handle that
        if delivery is None:
            messages.error(self.request,
                           "'Sorry, we were unable to sign you for that delivery, someone else may have already claimed it.'")
            return self.form_invalid(form)

        try:
            # If the meal request is still available setup the delivery
            self.update_delivery(form, delivery)
        except ValidationError as error:
            messages.error(self.request, error.messages[0])
            return redirect(self.success_url)

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


####################################################################
#                                                                  #
#                          Task list views                         #
#                                                                  #
####################################################################


class ChefIndexView(LoginRequiredMixin, GroupView, ListView):
    """View for chefs to see the meals they've signed up to cook"""
    model = MealDelivery
    context_object_name = "deliveries"
    queryset = MealDelivery.objects.exclude(status=Status.DELIVERED).order_by('date')
    template_name = "volunteers/chef_list.html"
    permission_group = 'Chefs'
    permission_group_redirect_url = reverse_lazy('volunteers:chef_application')

    def get_queryset(self):
        return self.queryset.filter(chef=self.request.user)


class DeliveryIndexView(LoginRequiredMixin, GroupView, ListView):
    """View for deliverers to see the meal requests they've signed up to deliver"""
    # model = MealDelivery
    template_name = "volunteers/delivery_list.html"
    permission_group = 'Deliverers'
    permission_group_redirect_url = reverse_lazy('volunteers:delivery_application')
    context_object_name = "deliveries"

    def get_queryset(self):
        meals = MealDelivery.objects.exclude(status=Status.DELIVERED).filter(deliverer=self.request.user)
        groceries = GroceryDelivery.objects.exclude(status=Status.DELIVERED).filter(deliverer=self.request.user)

        return sorted(chain(meals, groceries), key=lambda instance: instance.date)

    def post(self, request):
        if (request.POST['delivery_id'] and (
                request.POST['has_chef'] or request.POST['is_groceries'])):
            if request.POST['has_chef']:
                instance = MealDelivery.objects.get(uuid=request.POST['delivery_id'])
            else:
                instance = GroceryDelivery.objects.get(uuid=request.POST['delivery_id'])

            if instance.date <= date.today():
                instance.status = Status.DELIVERED
                instance.save()
                messages.success(
                    self.request,
                    'Marked delivery ID #%d to %s as complete! If this was a mistake please email us at %s as soon as possible.' %
                    (instance.pk, instance.request.address_1, settings.VOLUNTEER_COORDINATORS_EMAIL)
                )
            else:
                messages.error(
                    self.request,
                    'You can only mark deliveries complete after the assigned delivery date.'
                )
        else:
            messages.error(
                self.request,
                'Something went wrong, sorry about that!'
            )

        return redirect(self.request.get_full_path())


####################################################################
#                                                                  #
#                Volunteer application views                       #
#                                                                  #
####################################################################

class VolunteerApplicationView(FormView, UpdateView):
    success_url = reverse_lazy('volunteers:application_received')
    login_url = '/accounts/login/'

    def get_object(self):
        return Volunteer.objects.get(user=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        if VolunteerApplication.has_applied(self.request.user, self.role):
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        organizer_teams = form.cleaned_data.get("organizer_teams", "")
        application = VolunteerApplication.objects.create(
            user=self.request.user,
            role=self.role,
            organizer_teams=organizer_teams
        )
        application.send_confirmation_email()
        return super().form_valid(form)


class DeliveryApplicationView(LoginRequiredMixin, VolunteerApplicationView):
    role = VolunteerRoles.DELIVERERS
    form_class = DeliveryApplyForm
    template_name = "volunteers/delivery_application.html"


class ChefApplicationView(LoginRequiredMixin, VolunteerApplicationView):
    role = VolunteerRoles.CHEFS
    form_class = ChefApplyForm
    template_name = "volunteers/chef_application.html"


class OrganizerApplicationView(LoginRequiredMixin, VolunteerApplicationView):
    role = VolunteerRoles.ORGANIZERS
    form_class = OrganizerApplyForm
    template_name = "volunteers/organizer_application.html"


class ApplicationReceivedView(LoginRequiredMixin, TemplateView):
    template_name = "volunteers/application_received.html"


class VolunteerResourcesView(LoginRequiredMixin, TemplateView):
    template_name = "volunteers/volunteer_centre.html"
