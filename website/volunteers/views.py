from django.shortcuts import render
from recipients.models import MealRequest


def index(request):
    requests = MealRequest.objects.all()

    return render(request, "volunteers/index.html", {
        "anonymized_latitudes": list(map(lambda request: request.anonymized_latitude, requests)),
        "anonymized_longitudes": list(map(lambda request: request.anonymized_longitude, requests)),
    })
