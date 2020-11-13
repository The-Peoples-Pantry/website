from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from recipients.models import MealRequest


@login_required
def index(http_request):
    requests = MealRequest.objects.all()
    return render(http_request, "volunteers/index.html", {"requests": requests})
