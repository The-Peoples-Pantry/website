from textwrap import dedent
from django.views.generic.edit import FormView
from django.views.generic import DetailView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages


def index(request):
    return render(request, 'recipients/index.html')


def success(request):
    return render(request, 'recipients/success.html')


class HelpRequestView(FormView):
    success_url = reverse_lazy('recipients:success')

    def form_valid(self, form):
        instance = form.save()
        instance.send_confirmation_email()
        return super().form_valid(form)


class MealRequestView(HelpRequestView):
    template_name = 'recipients/new_meal_request.html'
    form_class = MealRequestForm

    def get(self, request):
        if MealRequest.requests_paused():
            return render(request, 'recipients/meal_paused.html')
        return super().get(request)

    def get_duplicate(self, form):
        if form.cleaned_data['on_behalf_of'] is False:
            phone = form.cleaned_data['phone_number']
            return MealRequest.has_open_request(phone)
        return False

    def form_valid(self, form):
        if self.get_duplicate(form):
            messages.warning(self.request, dedent("""
                We're sorry, it looks like we currently have an unfulfilled request on file for you already.
                Please give us some time to fulfill that request first before submitting another.
            """))
            return super().form_invalid(form)
        return super().form_valid(form)


class MealRequestDetail(LoginRequiredMixin, DetailView):
    model = MealRequest
    template_name = "recipients/meal_detail.html"
