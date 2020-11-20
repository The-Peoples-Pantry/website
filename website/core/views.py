from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.views.generic.edit import FormView, UpdateView

from .forms import UserCreationForm


class UserCreationView(FormView):
    form_class = UserCreationForm
    template_name = "core/signup.html"
    success_url = reverse_lazy('public:index')

    def form_valid(self, form):
        # Save the form to create the user
        # Then call login to make sure they're logged in before redirecting
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class UserProfileView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name']
    template_name = 'core/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile details updated')
        return super().form_valid(form)
