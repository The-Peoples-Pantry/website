from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from .forms import UserCreationForm


class UserCreationView(FormView):
    form_class = UserCreationForm
    template_name = "core/register.html"
    success_url = reverse_lazy('public:index')

    def form_valid(self, form):
        # Save the form to create the user
        # Then call login to make sure they're logged in before redirecting
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)
