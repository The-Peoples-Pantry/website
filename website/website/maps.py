import requests
from random import uniform, choice

from website.settings import MAPQUEST_API_KEY


class GeocoderException(Exception):
    pass


class Geocoder:
    API_BASE_URL = "http://mapquestapi.com/geocoding/v1"
    DEGREE_RANGE_LOWER = 0.001
    DEGREE_RANGE_HIGHER = 0.004

    def __init__(self, api_key=MAPQUEST_API_KEY):
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
