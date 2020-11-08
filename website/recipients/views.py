from django.views.generic.edit import FormView
from django.shortcuts import render
from django.urls import reverse_lazy
from .forms import MealRequestForm


def index(request):
    return render(request, 'recipients/index.html')


class MealRequestView(FormView):
    template_name = 'recipients/new.html'
    form_class = MealRequestForm
    success_url = reverse_lazy('recipients:success')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


def success(request):
    return render(request, 'recipients/success.html')
