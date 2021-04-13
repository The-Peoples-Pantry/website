import functools
import time

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import FormView, UpdateView, ContextMixin
from django.views.generic.list import MultipleObjectMixin

from core.models import group_names, has_group
from .forms import UserCreationForm, VolunteerProfileForm
from volunteers.models import Volunteer


class UserCreationView(FormView):
    form_class = UserCreationForm
    template_name = "core/signup.html"
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        # Save the form to create the user
        # Then call login to make sure they're logged in before redirecting
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class UserProfileView(LoginRequiredMixin, UpdateView):
    model = Volunteer
    form_class = VolunteerProfileForm
    template_name = 'core/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self):
        return Volunteer.objects.get(user=self.request.user)

    def get_pending_group_names(self, user):
        return list(user.volunteer_applications.filter(
            approved=False,
        ).values_list('role', flat=True))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = group_names(self.request.user)
        context["pending_groups"] = self.get_pending_group_names(self.request.user)
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Profile details updated')
        return super().form_valid(form)


class GroupRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return any(has_group(self.request.user, group) for group in self.get_permission_groups()) or self.request.user.is_staff

    def get_permission_groups(self):
        if hasattr(self, 'permission_groups'):
            return self.permission_groups
        elif hasattr(self, 'permission_group'):
            return (self.permission_group,)
        else:
            raise ImproperlyConfigured('GroupRequiredMixin requires either permission_group or permission_groups')

    def get_permission_group_redirect_url(self):
        default = reverse('profile')
        return getattr(self, 'permission_group_redirect_url', default)

    def handle_no_permission(self):
        return redirect(self.get_permission_group_redirect_url())


class LastVisitedMixin(MultipleObjectMixin, ContextMixin):
    """
    Provides context about when the page was last visited

    Stores a timestamp of last visit in the user's session and updates it each
    time the page is loaded. Exposes this timestamp in the context as the value
    "last visited".

    Counts how many objects in the object list were created later than our
    timestamp to determine the context value "new_since_last_visited".
    """
    def get_session_key(self):
        return self.__class__.__name__

    def new_since_last_visited(self):
        """Count how many of object_list are new (created) since a given timestamp"""
        return sum(self.last_visited < obj.created_at.timestamp() for obj in self.object_list)

    @functools.cached_property
    def last_visited(self):
        """Timestamp of the user's last visit to this page"""
        return self.request.session.get(self.get_session_key(), 0)

    def update_last_visited(self):
        """Update the timestamp of the user's last visit to this page"""
        self.request.session[self.get_session_key()] = time.time()

    def get_context_data(self, *args, **kwargs):
        context = {
            'last_visited': self.last_visited,
            'new_since_last_visited': self.new_since_last_visited(),
            **kwargs,
        }
        return super().get_context_data(**context)

    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        self.update_last_visited()
        return response
