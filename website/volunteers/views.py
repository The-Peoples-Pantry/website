import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.views.generic import ListView, TemplateView
from django.contrib.auth.models import User

from recipients.models import MealRequest, Delivery, Status
from public.views import GroupView, MapView
from .forms import DeliverySignupForm, ChefSignupForm, AcceptTermsForm
from .models import VolunteerApplication, VolunteerRoles


def delivery_success(request):
    return render(request, 'volunteers/delivery_success.html')


class ChefSignupView(LoginRequiredMixin, GroupView, FormView):
    """View for chefs to sign up to cook meal requests"""
    model = MealRequest
    template_name = "volunteers/chef_signup.html"
    form_class = ChefSignupForm
    success_url = reverse_lazy('volunteers:chef_signup')
    permission_group = 'Chefs'

    def get_context_data(self, alerts={}, **kwargs):
        context = super(ChefSignupView, self).get_context_data(**kwargs)

        meals = []
        for meal in MealRequest.objects.filter(delivery_date__isnull=True):
            meals.append({
                'meal': meal,
                'form': ChefSignupForm(instance=meal),
            })

        context['meals'] = meals
        context['alerts'] = alerts
        return context


    def create_delivery(self, data, user):
        user_object = User.objects.get(pk=user.id)
        meal_object = MealRequest.objects.get(uuid=data['uuid'])

        try:
            instance = Delivery.objects.get(request=meal_object)

        except Delivery.DoesNotExist as exception:
            if data['container_needed']:
                """Create another delivery object for
                just the containers"""
                container_instance = Delivery.objects.create(
                    request=meal_object,
                    chef=user_object,
                    status=Status.CHEF_ASSIGNED,
                    pickup_start=data['start_time'],
                    pickup_end=data['end_time'],
                    container_delivery=True
                )
                container_instance.user = user_object
                container_instance.save()

            meal_instance = Delivery.objects.create(
                request=meal_object,
                chef=user_object,
                status=Status.CHEF_ASSIGNED,
                pickup_start=data['start_time'],
                pickup_end=data['end_time']
            )
            meal_instance.user = user_object
            meal_instance.save()


    def post(self, request):
        data = request.POST
        alerts = {'success': False, 'errors': None}

        try:
            if data['delivery_date']:
                delivery_date = datetime.datetime.strptime(data['delivery_date'], '%Y-%m-%d')

                if delivery_date.date() >= datetime.datetime.today().date():
                    instance = MealRequest.objects.get(uuid=data['uuid'])
                    instance.delivery_date = data['delivery_date']
                    self.create_delivery(data, request.user)
                    instance.save()
                    alerts['success'] = True

                else:
                    alerts['error'] = "You tried to sign up to cook on "\
                        "%s, which is in the past. "\
                        "Please sign up for a date in the future."\
                        % data['delivery_date']

            else:
                alerts['error'] = "You didn't select a delivery date."

        except Exception as e:
            print("Exception raised while saving a chef sign-up: %s" % e)

        return render(request, self.template_name, self.get_context_data(alerts))


class ChefIndexView(LoginRequiredMixin, GroupView, ListView):
    """View for chefs to see the meals they've signed up to cook"""
    model = Delivery
    template_name = "volunteers/chef_list.html"
    context_object_name = "deliveries"
    permission_group = 'Chefs'

    def get_queryset(self):
        user = self.request.user
        return Delivery.objects.filter(
            chef=User.objects.get(pk=user.id)
        ).exclude(
            status=Status.DELIVERED
        ).order_by('request__delivery_date')



class DeliveryIndexView(LoginRequiredMixin, GroupView, ListView, MapView):
    model = Delivery
    template_name = "volunteers/delivery_list.html"
    context_object_name = "deliveries"
    permission_group = 'Deliverers'

    def get_queryset(self):
        user = self.request.user
        return Delivery.objects.filter(
            chef=User.objects.get(pk=user.id)
        ).exclude(
            status=Status.DELIVERED
        ).order_by('request__delivery_date')


class DeliverySignupView(LoginRequiredMixin, GroupView, FormView, MapView):
    model = Delivery
    template_name = "volunteers/delivery_signup.html"
    form_class = DeliverySignupForm
    success_url = reverse_lazy('volunteers:delivery_signup')
    permission_group = 'Deliverers'

    def get_context_data(self, alerts={}, **kwargs):
        context = super(DeliverySignupView, self).get_context_data(**kwargs)
        today = datetime.datetime.now().date()
        deliveries = []
        for delivery in Delivery.objects.filter(
            deliverer__isnull=True,
            request__delivery_date__range=[today,today + datetime.timedelta(days=7)]
        ).order_by('request__delivery_date'):
            delivery_date = delivery.request.delivery_date

            # If this is a container delivery, it needs to happen two days before the actual meal
            if delivery.container_delivery:
                delivery.request.delivery_date = delivery_date - datetime.timedelta(days=2)

            deliveries.append({
                'request': delivery.request,
                'delivery': delivery,
                'form': DeliverySignupForm(instance=delivery)
            })

        context['deliveries'] = deliveries
        context['alerts'] = alerts
        return context

    def post(self, request):
        data = request.POST
        alerts = {'success': False, 'errors': None}

        try:
            instance = Delivery.objects.get(uuid=data['uuid'])
            instance.dropoff_start = data['start_time']
            instance.dropoff_end = data['end_time']
            instance.deliverer = User.objects.get(pk=request.user.id)
            instance.status = Status.SCHEDULED
            instance.save()
            alerts['success'] = True

        except Exception as e:
            print("Exception raised while saving a delivery sign-up: %s" % e)

        return render(request, self.template_name, self.get_context_data(alerts))


class DeliveryApplicationView(LoginRequiredMixin, FormView):
    form_class = AcceptTermsForm
    template_name = "volunteers/delivery_application.html"
    success_url = reverse_lazy('volunteers:delivery_application_received')

    def get(self, request, *args, **kwargs):
        has_applied = VolunteerApplication.objects.filter(
            user=self.request.user,
            role=VolunteerRoles.DELIVERERS,
        ).exists()
        if has_applied:
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        VolunteerApplication.objects.create(
            user=self.request.user,
            role=VolunteerRoles.DELIVERERS,
        )
        return super().form_valid(form)


class DeliveryApplicationReceivedView(LoginRequiredMixin, TemplateView):
    template_name = "volunteers/delivery_application_received.html"


class ChefApplicationView(LoginRequiredMixin, FormView):
    form_class = AcceptTermsForm
    template_name = "volunteers/chef_application.html"
    success_url = reverse_lazy('volunteers:chef_application_received')

    def get(self, request, *args, **kwargs):
        has_applied = VolunteerApplication.objects.filter(
            user=self.request.user,
            role=VolunteerRoles.CHEFS,
        ).exists()
        if has_applied:
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        VolunteerApplication.objects.create(
            user=self.request.user,
            role=VolunteerRoles.CHEFS,
        )
        return super().form_valid(form)


class ChefApplicationReceivedView(LoginRequiredMixin, TemplateView):
    template_name = "volunteers/chef_application_received.html"