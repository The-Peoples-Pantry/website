from django.shortcuts import render
from recipients.models import MealRequest


def index(http_request):
    requests = MealRequest.objects.all()
    return render(http_request, "volunteers/index.html", {"requests": requests})
