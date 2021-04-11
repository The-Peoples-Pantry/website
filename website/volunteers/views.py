import logging
import time
from datetime import date
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.forms import ValidationError
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView, UpdateView
from django.views.generic import ListView, TemplateView
from django_filters.views import FilterView
from django.db.models.query_utils import Q

from core.models import has_group
from core.views import GroupRequiredMixin
from recipients.models import MealRequest, MealDelivery, Status
from website.maps import distance
from .forms import DelivererSignupForm, ChefSignupForm, ChefApplyForm, DeliveryApplyForm, OrganizerApplyForm
from .models import VolunteerApplication, VolunteerRoles, Volunteer
from .filters import ChefSignupFilter, DelivererSignupFilter


logger = logging.getLogger(__name__)


class ChefSignupView(LoginRequiredMixin, GroupRequiredMixin, FormView, FilterView):
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
                meal=form.cleaned_data['meal'],
            )
        else:
            MealDelivery.objects.create(
                request=meal_request,
                chef=self.request.user,
                status=Status.CHEF_ASSIGNED,
                date=form.cleaned_data['delivery_date'],
                pickup_start=form.cleaned_data['pickup_start'],
                pickup_end=form.cleaned_data['pickup_end'],
                meal=form.cleaned_data['meal'],
            )


class DelivererSignupView(LoginRequiredMixin, GroupRequiredMixin, FormView, FilterView):
    """View for deliverers to sign up to deliver meal requests"""
    template_name = "volunteers/delivery_signup.html"
    form_class = DelivererSignupForm
    permission_group = 'Deliverers'
    permission_group_redirect_url = reverse_lazy('volunteers:delivery_application')
    filterset_class = DelivererSignupFilter
    queryset = MealRequest.objects.not_delivered().exclude(delivery_date__isnull=True).filter(deliverer__isnull=True)
    ordering = 'delivery_date'

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
        context = super().get_context_data(**kwargs)
        form_class = self.get_form_class()
        last_visited = self.get_and_set_last_visited()
        context["meal_request_form_pairs"] = [
            (meal_request, form_class(initial={
                'id': meal_request.id,
                'pickup_start': meal_request.pickup_start,
                'pickup_end': meal_request.pickup_end
            }))
            for meal_request in self.object_list
        ]
        context["new_since_last_visited"] = self.new_since(last_visited)
        context["last_visited"] = last_visited
        return context

    def form_invalid(self, form):
        if form.non_field_errors():
            messages.error(self.request, form.non_field_errors())
        return redirect(self.success_url)

    def form_valid(self, form):
        # First fetch the associated MealRequest
        meal_request = self.get_meal_request(form)

        # It's possible that someone else has signed up for it, so handle that
        if meal_request is None:
            messages.error(
                self.request,
                "Sorry, we were unable to sign you for that request, someone else may have already claimed it.",
            )
            return self.form_invalid(form)

        try:
            # If the meal request is still available, update it from the form values
            self.update_meal_request(form, meal_request)
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

    def update_meal_request(self, form, meal_request):
        meal_request.dropoff_start = form.cleaned_data['dropoff_start']
        meal_request.dropoff_end = form.cleaned_data['dropoff_end']
        meal_request.deliverer = self.request.user
        meal_request.status = Status.DRIVER_ASSIGNED
        meal_request.save()


####################################################################
#                                                                  #
#                          Task list views                         #
#                                                                  #
####################################################################


class ChefIndexView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    """View for chefs to see the meals they've signed up to cook"""
    model = MealDelivery
    ordering = 'date'
    context_object_name = "deliveries"
    template_name = "volunteers/chef_list.html"
    permission_group = 'Chefs'
    permission_group_redirect_url = reverse_lazy('volunteers:chef_application')

    def get_queryset(self):
        return super().get_queryset().filter(chef=self.request.user)


class DeliveryIndexView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    """View for deliverers to see the meal requests they've signed up to deliver"""
    model = MealDelivery
    ordering = 'date'
    template_name = "volunteers/delivery_list.html"
    permission_group = 'Deliverers'
    permission_group_redirect_url = reverse_lazy('volunteers:delivery_application')
    context_object_name = "deliveries"

    def get_queryset(self):
        return super().get_queryset().filter(deliverer=self.request.user)

    def post(self, request):
        instance = MealDelivery.objects.get(id=request.POST['delivery_id'])

        # Ensure that this was submitted by the deliverer
        # Prevents someone abusing this POST endpoint with delivery_ids that don't "belong" to them
        if instance.deliverer != request.user:
            raise PermissionDenied

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


class ResourcesView(LoginRequiredMixin, TemplateView):
    template_name = "volunteers/resources.html"
