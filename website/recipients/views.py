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


def new(request):
    if request.method == 'POST':
        form = MealRequestForm(request.POST)
        request_uuid = uuid.uuid4()
        if form.is_valid():
            return render(request, 'recipients/confirmation.html', {"name": request.POST['name'], "uuid": request_uuid})

    return render(request, 'recipients/new.html', {"request_form": MealRequestForm()})
