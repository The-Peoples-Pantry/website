import functools
import logging
import re
import urllib.parse
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from website.maps import Geocoder, GeocoderException

logger = logging.getLogger(__name__)


def get_sentinel_user():
    return get_user_model().objects.get_or_create(username="deleted")[0]


def has_group(user, group_name: str):
    """Test whether the user is in a group with the given name"""
    return user.groups.filter(name=group_name).exists()


def group_names(user):
    """Returns a list of group names for the user"""
    return list(user.groups.all().values_list("name", flat=True))


def validate_toronto_postal_code(value):
    """Toronto postal codes start with an 'M'"""
    if value is None:
        return

    if not value.upper().startswith("M"):
        raise ValidationError(
            "This postal code falls outside of the regions that we support"
        )


class TelephoneInput(forms.TextInput):
    input_type = "tel"

    def __init__(self, attrs=None):
        attrs = {} if attrs is None else attrs
        super().__init__(
            attrs={
                "pattern": r"\(?[0-9]{3}\)?[- ]?[0-9]{3}[- ]?[0-9]{4}",
                "title": "Telephone input in the form xxx-xxx-xxxx",
                **attrs,
            }
        )


class TelephoneFormField(forms.CharField):
    widget = TelephoneInput

    def clean(self, value):
        value = super().clean(value)
        if value is None:
            return value

        # Strip any extra characters from the phone number like ), (, space, or -
        value = re.sub(r"[^0-9]", "", value)

        # Then, re-format as 555-555-5555, as long as the right number of digits
        if len(value) == 10:
            value = f"{value[0:3]}-{value[3:6]}-{value[6:10]}"

        return value


class TelephoneField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("help_text", "Use the format 555-555-5555")
        kwargs.setdefault("max_length", settings.PHONE_NUMBER_LENGTH)
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": TelephoneFormField,
                **kwargs,
            }
        )


class Cities(models.TextChoices):
    EAST_YORK = "East York", "East York"
    ETOBICOKE = "Etobicoke", "Etobicoke"
    NORTH_YORK = "North York", "North York"
    SCARBOROUGH = "Scarborough", "Scarborough"
    TORONTO = "Toronto", "Toronto"
    YORK = "York", "York"


class ContactMixin(models.Model):
    class Meta:
        abstract = True

    name = models.CharField("Full name", max_length=settings.NAME_LENGTH)
    phone_number = TelephoneField("Phone number")
    email = models.EmailField("Email address")


class DemographicMixin(models.Model):
    class Meta:
        abstract = True

    DEMOGRAPHIC_ATTRIBUTES = (
        "bipoc",
        "lgbtq",
        "has_disability",
        "immigrant_or_refugee",
        "housing_issues",
        "sex_worker",
        "single_parent",
        "senior",
    )

    def in_any_demographic(self):
        """Are they a member of any of our tracked demographics?"""
        return any(
            getattr(self, attribute) for attribute in self.DEMOGRAPHIC_ATTRIBUTES
        )

    bipoc = models.BooleanField("Black, Indigenous, and People of Colour (BIPOC)")
    lgbtq = models.BooleanField(
        "Lesbian, Gay, Bisexual, Trans, Queer (LGBTQ), gender non-conforming or non-binary"
    )
    has_disability = models.BooleanField("Living with disabilities")
    immigrant_or_refugee = models.BooleanField("Newly arrived immigrant or refugee")
    housing_issues = models.BooleanField(
        "Precariously housed (no fixed address, living in a shelter, etc.)"
    )
    sex_worker = models.BooleanField("Sex worker")
    single_parent = models.BooleanField("Single parent")
    senior = models.BooleanField("Senior citizen")


class TimestampsMixin(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AddressMixin(models.Model):
    class Meta:
        abstract = True

    address_1 = models.CharField(
        "Address line 1",
        help_text="Street name and number",
        max_length=settings.ADDRESS_LENGTH,
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
        "Postal code", max_length=settings.POSTAL_CODE_LENGTH
    )
    anonymized_latitude = models.FloatField(
        default=43.651070, blank=True
    )  # default: Toronto latitude
    anonymized_longitude = models.FloatField(
        default=-79.347015, blank=True
    )  # default: Toronto longitude

    @property
    def province(self):
        return "Ontario"

    @property
    def address(self):
        return f"{self.address_1} {self.address_2} {self.city} {self.province} {self.postal_code}"

    @property
    def address_link(self):
        params = urllib.parse.urlencode({"api": 1, "query": self.address})
        return f"https://www.google.com/maps/search/?{params}"

    @property
    def directions_link(self):
        if self.chef is None:
            return None

        params = urllib.parse.urlencode(
            {
                "api": 1,
                "destination": self.chef.volunteer.address,
                "origin": self.address,
            }
        )
        return f"https://www.google.com/maps/dir/?{params}"

    @property
    def anonymous_address_link(self):
        params = urllib.parse.urlencode(
            {
                "api": 1,
                "query": f"{self.anonymized_latitude},{self.anonymized_longitude}",
            }
        )
        return f"https://www.google.com/maps/search/?{params}"

    @property
    def anonymous_map_embed(self):
        params = urllib.parse.urlencode(
            {
                "key": settings.GOOGLE_MAPS_PRODUCTION_KEY,
                "q": f"{self.anonymized_latitude},{self.anonymized_longitude}",
            }
        )
        return f"https://www.google.com/maps/embed/v1/place?{params}"

    @property
    def coordinates(self):
        return (self.anonymized_latitude, self.anonymized_longitude)

    @functools.cached_property
    def fetched_coordinates(self):
        return Geocoder().geocode_anonymized(self.address)

    def update_coordinates(self):
        """Updates, but does not commit, anonymized coordinates on the instance"""
        try:
            latitude, longitude = self.fetched_coordinates
            self.anonymized_latitude = latitude
            self.anonymized_longitude = longitude
        except GeocoderException:
            logger.exception("Error when updating coordinates for %d", self.id)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__initial_address = self.address

    def save(self, *args, **kwargs):
        # If the address has been updated, update the coordinates too
        if self._address_has_changed():
            self.update_coordinates()
        super().save(*args, **kwargs)

    def _address_has_changed(self):
        return self.__initial_address != self.address


class TorontoAddressMixin(AddressMixin):
    class Meta:
        abstract = True

    postal_code = models.CharField(
        "Postal code",
        validators=[validate_toronto_postal_code],
        max_length=settings.POSTAL_CODE_LENGTH,
    )
