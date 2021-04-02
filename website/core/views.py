from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import FormView, UpdateView

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
        return has_group(self.request.user, self.permission_group) or self.request.user.is_staff

    def get_permission_group_redirect_url(self):
        default = reverse('profile')
        return getattr(self, 'permission_group_redirect_url', default)

    def handle_no_permission(self):
        return redirect(self.get_permission_group_redirect_url())
