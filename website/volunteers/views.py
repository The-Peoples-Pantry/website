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

from core.models import has_group
from core.views import GroupRequiredMixin
from recipients.models import MealRequest, Status
from website.maps import distance
from .forms import DelivererSignupForm, ChefSignupForm, ChefApplyForm, DeliveryApplyForm, OrganizerApplyForm
from .models import VolunteerApplication, VolunteerRoles, Volunteer
from .filters import ChefSignupFilter, DelivererSignupFilter


logger = logging.getLogger(__name__)


class ChefSignupListView(LoginRequiredMixin, GroupRequiredMixin, FilterView):
    """View for chefs to sign up to cook meal requests"""
    template_name = "volunteers/chef_signup_list.html"
    permission_group = 'Chefs'
    permission_group_redirect_url = reverse_lazy('volunteers:chef_application')
    filterset_class = ChefSignupFilter
    queryset = MealRequest.objects.not_delivered().filter(chef__isnull=True)
    ordering = 'created_at'

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
        context = super().get_context_data(**kwargs)
        last_visited = self.get_and_set_last_visited()
        context["object_contexts"] = [
            {
                "meal_request": meal_request,
                "form": ChefSignupForm(instance=meal_request),
                "distance": distance(meal_request.coordinates, self.request.user.volunteer.coordinates),
            }
            # self.object_list is a MealRequest queryset pre-filtered by ChefSignupFilter
            for meal_request in self.object_list
        ]
        context["last_visited"] = last_visited
        context["new_since_last_visited"] = self.new_since(last_visited)
        context["can_deliver"] = self.can_deliver(self.request.user)
        return context


class ChefSignupView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    permission_group = 'Chefs'
    permission_group_redirect_url = reverse_lazy('volunteers:chef_application')
    form_class = ChefSignupForm
    queryset = MealRequest.objects.not_delivered().filter(chef__isnull=True)
    template_name = "volunteers/chef_signup.html"
    context_object_name = "meal_request"
    success_url = reverse_lazy('volunteers:chef_signup_list')

    def can_deliver(self, user):
        return has_group(user, 'Deliverers')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_deliver"] = self.can_deliver(self.request.user)
        context["distance"] = distance(self.object.coordinates, self.request.user.volunteer.coordinates)
        return context

    def form_valid(self, form):
        self.object.chef = self.request.user
        if form.cleaned_data['can_deliver']:
            self.object.deliverer = self.request.user
            self.object.status = Status.DRIVER_ASSIGNED
        else:
            self.object.status = Status.CHEF_ASSIGNED
        self.object.save()
        messages.success(self.request, 'Successfully signed up!')
        return super().form_valid(form)


class DelivererSignupListView(LoginRequiredMixin, GroupRequiredMixin, FilterView):
    """View for deliverers to sign up to deliver meal requests"""
    template_name = "volunteers/delivery_signup_list.html"
    permission_group = 'Deliverers'
    permission_group_redirect_url = reverse_lazy('volunteers:delivery_application')
    filterset_class = DelivererSignupFilter
    queryset = MealRequest.objects.not_delivered().exclude(delivery_date__isnull=True).filter(deliverer__isnull=True)
    ordering = 'delivery_date'

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
        last_visited = self.get_and_set_last_visited()
        context["meal_request_form_pairs"] = [
            (meal_request, DelivererSignupForm(instance=meal_request))
            for meal_request in self.object_list
        ]
        context["new_since_last_visited"] = self.new_since(last_visited)
        context["last_visited"] = last_visited
        return context


class DelivererSignupView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    form_class = DelivererSignupForm
    permission_group = 'Deliverers'
    permission_group_redirect_url = reverse_lazy('volunteers:delivery_application')
    queryset = MealRequest.objects.not_delivered().exclude(delivery_date__isnull=True).filter(deliverer__isnull=True)
    template_name = "volunteers/delivery_signup.html"
    context_object_name = "meal_request"
    success_url = reverse_lazy('volunteers:delivery_signup_list')

    def form_valid(self, form):
        self.object.deliverer = self.request.user
        self.object.status = Status.DRIVER_ASSIGNED
        self.object.save()
        messages.success(self.request, 'Successfully signed up!')
        return super().form_valid(form)

####################################################################
#                                                                  #
#                          Task list views                         #
#                                                                  #
####################################################################


class ChefIndexView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    """View for chefs to see the meals they've signed up to cook"""
    model = MealRequest
    ordering = 'delivery_date'
    context_object_name = "meal_requests"
    template_name = "volunteers/chef_list.html"
    permission_group = 'Chefs'
    permission_group_redirect_url = reverse_lazy('volunteers:chef_application')

    def get_queryset(self):
        return super().get_queryset().filter(chef=self.request.user)


class DeliveryIndexView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    """View for deliverers to see the meal requests they've signed up to deliver"""
    model = MealRequest
    ordering = 'delivery_date'
    context_object_name = "meal_requests"
    template_name = "volunteers/delivery_list.html"
    permission_group = 'Deliverers'
    permission_group_redirect_url = reverse_lazy('volunteers:delivery_application')

    def get_queryset(self):
        return super().get_queryset().filter(deliverer=self.request.user)

    def post(self, request):
        meal_request = self.get_queryset().get(id=request.POST['meal_request_id'])

        # Ensure that this was submitted by the deliverer
        # Prevents someone abusing this POST endpoint with meal_request_ids that don't "belong" to them
        if meal_request.deliverer != request.user:
            raise PermissionDenied

        if meal_request.delivery_date <= date.today():
            meal_request.status = Status.DELIVERED
            meal_request.save()
            messages.success(
                self.request,
                'Marked delivery ID #%d to %s as complete! If this was a mistake please email us at %s as soon as possible.' %
                (meal_request.pk, meal_request.address, settings.VOLUNTEER_COORDINATORS_EMAIL)
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
