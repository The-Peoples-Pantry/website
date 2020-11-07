import uuid
from django.shortcuts import render
from django.forms import ModelForm
from .models import MealRequest


class MealRequestForm(ModelForm):
    class Meta:
        model = MealRequest
        exclude = []


def index(request):
    return render(request, 'recipients/index.html')


def new(http_request):
    if http_request.method == 'POST':
        form = MealRequestForm(http_request.POST)
        if form.is_valid():
            request_uuid = uuid.uuid4()
            form.save()
            return render(http_request, 'recipients/confirmation.html',
                          {"name": http_request.POST['name'], "uuid": request_uuid})

    return render(http_request, 'recipients/new.html', {"request_form": MealRequestForm()})
