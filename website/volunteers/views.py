import logging
from datetime import date
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView, UpdateView
from django.views.generic import ListView, TemplateView
from django_filters.views import FilterView

from core.views import GroupRequiredMixin, LastVisitedMixin
from recipients.models import MealRequest
from .forms import DelivererSignupForm, ChefSignupForm, ChefTaskForm, ChefApplyForm, DelivererApplyForm, OrganizerApplyForm
from .models import VolunteerApplication, VolunteerRoles, Volunteer
from .filters import ChefSignupFilter, DelivererSignupFilter


logger = logging.getLogger(__name__)


class ChefSignupListView(LoginRequiredMixin, GroupRequiredMixin, LastVisitedMixin, FilterView):
    """View for chefs to sign up to cook meal requests"""
    template_name = "volunteers/chef_signup_list.html"
    permission_group = 'Chefs'
    permission_group_redirect_url = reverse_lazy('volunteers:chef_application')
    filterset_class = ChefSignupFilter
    queryset = MealRequest.objects.available_for_chef_signup()

    def get_queryset(self):
        return super().get_queryset().with_delivery_distance(chef=self.request.user).order_by('delivery_distance')

    @property
    def extra_context(self):
        return {
            'forms': [ChefSignupForm(instance=meal_request) for meal_request in self.object_list],
        }


class ChefSignupView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    permission_group = 'Chefs'
    permission_group_redirect_url = reverse_lazy('volunteers:chef_application')
    form_class = ChefSignupForm
    queryset = MealRequest.objects.available_for_chef_signup()
    template_name = "volunteers/chef_signup.html"
    context_object_name = "meal_request"
    success_url = reverse_lazy('volunteers:chef_signup_list')

    def get_queryset(self):
        return super().get_queryset().with_delivery_distance(chef=self.request.user)

    def form_valid(self, form):
        self.object.chef = self.request.user
        if form.cleaned_data['can_deliver']:
            self.object.deliverer = self.request.user
            self.object.status = MealRequest.Status.DRIVER_ASSIGNED
        else:
            self.object.status = MealRequest.Status.CHEF_ASSIGNED
        self.object.save()
        messages.success(self.request, 'Successfully signed up!')
        return super().form_valid(form)


class DelivererSignupListView(LoginRequiredMixin, GroupRequiredMixin, LastVisitedMixin, FilterView):
    """View for deliverers to sign up to deliver meal requests"""
    template_name = "volunteers/deliverer_signup_list.html"
    permission_group = 'Deliverers'
    permission_group_redirect_url = reverse_lazy('volunteers:deliverer_application')
    filterset_class = DelivererSignupFilter
    queryset = MealRequest.objects.available_for_deliverer_signup().with_delivery_distance()
    ordering = 'delivery_date'

    @property
    def extra_context(self):
        return {
            'forms': [DelivererSignupForm(instance=meal_request) for meal_request in self.object_list],
        }


class DelivererSignupView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    form_class = DelivererSignupForm
    permission_group = 'Deliverers'
    permission_group_redirect_url = reverse_lazy('volunteers:deliverer_application')
    queryset = MealRequest.objects.available_for_deliverer_signup().with_delivery_distance()
    template_name = "volunteers/deliverer_signup.html"
    context_object_name = "meal_request"
    success_url = reverse_lazy('volunteers:deliverer_signup_list')

    def form_valid(self, form):
        self.object.deliverer = self.request.user
        self.object.status = MealRequest.Status.DRIVER_ASSIGNED
        self.object.save()
        messages.success(self.request, 'Successfully signed up!')
        return super().form_valid(form)

####################################################################
#                                                                  #
#                          Task list views                         #
#                                                                  #
####################################################################


class ChefTaskListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    """View for chefs to see the meals requests they've signed up for"""
    model = MealRequest
    ordering = '-delivery_date'
    context_object_name = "meal_requests"
    template_name = "volunteers/chef_list.html"
    permission_group = 'Chefs'
    permission_group_redirect_url = reverse_lazy('volunteers:chef_application')

    def get_queryset(self):
        return super().get_queryset().filter(chef=self.request.user)

    @property
    def extra_context(self):
        return {
            'delivered': {
                'forms': [ChefTaskForm(instance=meal_request) for meal_request in self.object_list.delivered()],
            },
            'not_delivered': {
                'forms': [ChefTaskForm(instance=meal_request) for meal_request in self.object_list.not_delivered()],
            }
        }


class ChefTaskView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    """View for chefs to edit a meal request they've signed up for"""
    model = MealRequest
    form_class = ChefTaskForm
    permission_group = 'Chefs'
    permission_group_redirect_url = reverse_lazy('volunteers:chef_application')
    template_name = "volunteers/chef_task.html"
    context_object_name = "meal_request"
    success_url = reverse_lazy('volunteers:chef_list')

    def get_queryset(self):
        return super().get_queryset().filter(chef=self.request.user)

    def form_valid(self, *args, **kwargs):
        messages.success(self.request, f"Updated details for Request #{self.object.id}")
        return super().form_valid(*args, **kwargs)


class DelivererTaskListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    """View for deliverers to see the meal requests they've signed up for"""
    model = MealRequest
    ordering = '-delivery_date'
    context_object_name = "meal_requests"
    template_name = "volunteers/deliverer_list.html"
    permission_groups = ('Chefs', 'Deliverers')
    permission_group_redirect_url = reverse_lazy('volunteers:deliverer_application')

    def get_queryset(self):
        return super().get_queryset().filter(deliverer=self.request.user)

    def post(self, request):
        meal_request = self.get_queryset().get(id=request.POST['meal_request_id'])

        if meal_request.delivery_date <= date.today():
            meal_request.status = MealRequest.Status.DELIVERED
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


class DelivererApplicationView(LoginRequiredMixin, VolunteerApplicationView):
    role = VolunteerRoles.DELIVERERS
    form_class = DelivererApplyForm
    template_name = "volunteers/deliverer_application.html"


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
