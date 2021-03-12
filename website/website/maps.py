import glob
import math
from random import uniform, choice

import geojson
import requests
import shapely.geometry
import shapely.prepared

from django.conf import settings


class GeocoderException(Exception):
    pass


class GroceryDeliveryArea:
    @property
    def geojson_dir(self):
        return settings.BASE_DIR / 'data'

    @property
    def geojson_filenames(self):
        return glob.glob(f"{self.geojson_dir}/*.geojson")

    @property
    def feature_collections(self):
        for filename in self.geojson_filenames:
            yield self.load_feature_collection(filename)

    @property
    def regions(self):
        for feature_collection in self.feature_collections:
            coordinates = geojson.utils.coords(feature_collection)
            polygon = shapely.geometry.Polygon(coordinates).convex_hull
            prepared_polygon = shapely.prepared.prep(polygon)
            yield prepared_polygon

    def load_feature_collection(self, filename):
        with open(filename) as f:
            return geojson.load(f)

    def includes(self, longitude, latitude):
        point = shapely.geometry.Point(longitude, latitude)
        return any(region.contains(point) for region in self.regions)


class Geocoder:
    API_BASE_URL = "http://mapquestapi.com/geocoding/v1"
    DEGREE_RANGE_LOWER = 0.001
    DEGREE_RANGE_HIGHER = 0.004

    def __init__(self, api_key=settings.MAPQUEST_API_KEY):
        self.api_key = api_key

    def geocode_anonymized(self, address):
        """Given an address, return an anonymized latitude & longitude"""
        latitude, longitude = self.geocode(address)
        latitude += self.generate_noise()
        longitude += self.generate_noise()
        return round(latitude, 3), round(longitude, 3)

    def geocode(self, address):
        """Given an address, return the latitude & longitude"""
        try:
            response = requests.get(
                f"{self.API_BASE_URL}/address",
                params={"key": self.api_key, "location": address}
            )
            response.raise_for_status()
            lat_lng = response.json()["results"][0]["locations"][0]["latLng"]
            return lat_lng["lat"], lat_lng["lng"]
        except Exception as e:
            raise GeocoderException from e

    def generate_noise(self):
        """Generate a random value in range, and randomly positive or negative"""
        return uniform(self.DEGREE_RANGE_LOWER, self.DEGREE_RANGE_HIGHER) * choice([-1, 1])


def distance(point1, point2) -> float:
    """
    Roughly approximate the distance between two latitude-longitude pairs in km

    Roughly being the keyword here. We're doing a couple of things for simplicity:
    - We assume a constant latitude degree length of 110km (in truth it varies 110-111)
    - We use Euclidean distance which is meant for planes, but will work for a spheroid over small distances

    A more complete solution would use the haversine formula, but we're going for simplicity
    Since we are calculating over small distances, the error is negligible (within a few metres)

    https://en.wikipedia.org/wiki/Euclidean_distance
    https://en.wikipedia.org/wiki/Latitude#Length_of_a_degree_of_latitude
    https://en.wikipedia.org/wiki/Haversine_formula
    """
    lat1, long1 = point1
    lat2, long2 = point2
    degree_length = 110
    return degree_length * math.sqrt(math.pow(lat1 - lat2, 2) + math.pow(long1 - long2, 2))
