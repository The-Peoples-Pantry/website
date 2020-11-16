import requests
from random import uniform, choice

from website.settings import MAPQUEST_API_KEY

DEGREE_RANGE_LOWER = 0.0004
DEGREE_RANGE_HIGHER = 0.0008


def mapquest_api_url(resource):
    # NOTE: open.mapquestapi.com relies on OSM data and does NOT support includeNearestIntersection for reverse coding
    return "http://mapquestapi.com/geocoding/v1" + resource


def geocode(address, api_key=MAPQUEST_API_KEY):
    response = requests.get(
        mapquest_api_url("/address"),
        params={
            "key": api_key,
            "location": address
        }
    )

    if response.status_code != 200:
        return None
    else:
        lat_lng = response.json()["results"][0]["locations"][0]["latLng"]
        return lat_lng["lat"], lat_lng["lng"]


def reverse_geocode(coords, api_key=MAPQUEST_API_KEY, include_nearest_intersection=False):
    return requests.get(
        mapquest_api_url("/reverse"),
        params={
            "key": api_key,
            "location": f"{coords[0]},{coords[1]}",
            "includeNearestIntersection": "true" if include_nearest_intersection else "false"
        }
    )


def geocode_anonymized(address, api_key=MAPQUEST_API_KEY):
    lat, long = geocode(address, api_key)
    lat += uniform(DEGREE_RANGE_LOWER, DEGREE_RANGE_HIGHER) * choice([-1, 1])
    long += uniform(DEGREE_RANGE_LOWER, DEGREE_RANGE_HIGHER) * choice([-1, 1])

    return lat, long


def nearest_intersection(address, api_key=MAPQUEST_API_KEY):
    return reverse_geocode(geocode(address), api_key=api_key, include_nearest_intersection=True) \
        .json()["results"][0]["locations"][0]["nearestIntersection"]
