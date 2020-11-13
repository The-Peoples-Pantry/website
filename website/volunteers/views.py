from django.shortcuts import render
from recipients.models import MealRequest


def index(http_request):
    requests = MealRequest.objects.all()

    return render(http_request, "volunteers/index.html", {
        "anonymized_latitudes": list(map(lambda request: request.anonymized_latitude, requests)),
        "anonymized_longitudes": list(map(lambda request: request.anonymized_longitude, requests)),
        "requests": requests,
    })
