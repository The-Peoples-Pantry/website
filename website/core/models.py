from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
from website.maps import Geocoder, GeocoderException


def get_sentinel_user():
    return get_user_model().objects.get_or_create(username='deleted')[0]


def has_group(user, group_name: str):
    """Test whether the user is in a group with the given name"""
    return user.groups.filter(name=group_name).exists()


def group_names(user):
    """Returns a list of group names for the user"""
    return list(user.groups.all().values_list('name', flat=True))


class Cities(models.TextChoices):
    EAST_YORK = 'East York', 'East York'
    ETOBICOKE = 'Etobicoke', 'Etobicoke'
    NORTH_YORK = 'North York', 'North York'
    SCARBOROUGH = 'Scarborough', 'Scarborough'
    TORONTO = 'Toronto', 'Toronto'
    YORK = 'York', 'York'


class ContactInfo(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(
        "Full name",
        max_length=settings.NAME_LENGTH
    )
    phone_number = models.CharField(
        "Phone number",
        help_text="Use the format 555-555-5555",
        max_length=settings.PHONE_NUMBER_LENGTH,
    )
    email = models.EmailField("Email address")
    address_1 = models.CharField(
        "Address line 1",
        help_text="Street name and number",
        max_length=settings.ADDRESS_LENGTH
    )
    address_2 = models.CharField(
        "Address line 2",
        help_text="Apartment, Unit, or Suite number",
        max_length=settings.ADDRESS_LENGTH,
        blank=True,
    )
    city = models.CharField(
        "City",
        max_length=settings.CITY_LENGTH,
        choices=Cities.choices,
        default=Cities.TORONTO,
    )
    postal_code = models.CharField(
        "Postal code",
        max_length=settings.POSTAL_CODE_LENGTH
    )
    anonymized_latitude = models.FloatField(default=43.651070, blank=True)  # default: Toronto latitude
    anonymized_longitude = models.FloatField(default=-79.347015, blank=True)  # default: Toronto longitude

    @property
    def address(self):
        return f"{self.address_1} {self.address_2} {self.city} {self.postal_code}"

    @property
    def address_link(self):
        address = urllib.parse.quote(self.address)
        return f"https://www.google.com/maps/place/{address}"

    @property
    def anonymous_address_link(self):
        return f"https://www.google.com/maps/place/{self.anonymized_latitude},{self.anonymized_longitude}"

    @property
    def anonymous_map_embed(self):
        return f"https://www.google.com/maps/embed/v1/place?key={ settings.GOOGLE_MAPS_PRODUCTION_KEY }&q={self.anonymized_latitude},{self.anonymized_longitude}"

    @property
    def coordinates(self):
        return (self.anonymized_latitude, self.anonymized_longitude)

    def update_coordinates(self):
        """Updates, but does not commit, anonymized coordinates on the instance"""
        try:
            latitude, longitude = Geocoder().geocode_anonymized(self.address)
            self.anonymized_latitude = latitude
            self.anonymized_longitude = longitude
        except GeocoderException:
            logger.exception("Error when updating coordinates for %d", self.uuid)

    def save(self, *args, **kwargs):
        # Whenever the model is updated, make sure coordinates are updated too
        self.update_coordinates()
        super().save(*args, **kwargs)


class GroceryPickupAddress(ContactInfo):
    name = models.CharField(
        "Name of volunteer responsible for this address",
        max_length=settings.NAME_LENGTH
    )
    phone_number = models.CharField(
        "Phone number of volunteer responsible for this address",
        help_text="Use the format 555-555-5555",
        max_length=settings.PHONE_NUMBER_LENGTH,
    )
    email = models.EmailField(
        "Email address if applicable",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.address_1
