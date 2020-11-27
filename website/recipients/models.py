import datetime
import logging
from textwrap import dedent
import urllib.parse
import uuid
from django.core.mail import send_mail
from django.db import models
from django.conf import settings
from django.urls import reverse_lazy

from core.models import get_sentinel_user
from website.maps import Geocoder, GeocoderException


logger = logging.getLogger(__name__)


class Cities(models.TextChoices):
    AJAX = 'Ajax', 'Ajax'
    AURORA = 'Aurora', 'Aurora'
    BRAMPTON = 'Brampton', 'Brampton'
    BROCK = 'Brock', 'Brock'
    CALEDON = 'Caledon', 'Caledon'
    CLARINGTON = 'Clarington', 'Clarington'
    EAST_GWILIMBURY = 'East Gwilimbury', 'East Gwilimbury'
    EAST_YORK = 'East York', 'East York'
    ETOBICOKE = 'Etobicoke', 'Etobicoke'
    GEORGINA = 'Georgina', 'Georgina'
    KING = 'King', 'King'
    MAPLE = 'Maple', 'Maple'
    MARKHAM = 'Markham', 'Markham'
    MISSISSAUGA = 'Mississauga', 'Mississauga'
    NEWMARKET = 'Newmarket', 'Newmarket'
    NORTH_YORK = 'North York', 'North York'
    OSHAWA = 'Oshawa', 'Oshawa'
    PICKERING = 'Pickering', 'Pickering'
    RICHMOND_HILL = 'Richmond Hill', 'Richmond Hill'
    SCARBOROUGH = 'Scarborough', 'Scarborough'
    SCUGOG = 'Scugog', 'Scugog'
    STOUFFVILLE = 'Stouffville', 'Stouffville'
    THORNHILL = 'Thornhill', 'Thornhill'
    TORONTO = 'Toronto', 'Toronto (downtown, east/west ends)'
    UXBRIDGE = 'Uxbridge', 'Uxbridge'
    VAUGHAN = 'Vaughan', 'Vaughan'
    WHITBY = 'Whitby', 'Whitby'
    YORK = 'York', 'York'


class Vegetables(models.TextChoices):
    CARROTS = 'Carrots'
    GARLIC = 'Garlic'
    ONIONS = 'Onions'
    POTATOES = 'Potatoes'
    SPINACH = 'Spinach'


class Fruits(models.TextChoices):
    APPLES = 'Apples'
    BANANAS = 'Bananas'
    ORANGES = 'Oranges'


class Protein(models.TextChoices):
    BEEF = 'Beef'
    CHICKEN = 'Chicken'
    TOFU = 'Tofu'
    EGGS = 'Eggs'


class Grains(models.TextChoices):
    BLACK_BEANS = 'Black Beans'
    CHICKPEAS = 'Chickpeas'
    LENTILS = 'Lentils'
    RICE = 'Rice'
    PASTA = 'Pasta'


class Condiments(models.TextChoices):
    FLOUR = 'Flour'
    SUGAR = 'Sugar'
    TOMATO_SAUCE = 'Tomato Sauce'


class Dairy(models.TextChoices):
    MILK = 'Milk'
    ALMOND_MILK = 'Almond Milk'


class AddressModel(models.Model):
    class Meta:
        abstract = True

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
        return f"https://www.google.com/maps/embed/v1/place?key={ settings.GOOGLE_MAPS_EMBED_KEY }&q={self.anonymized_latitude},{self.anonymized_longitude}"

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


class HelpRequest(AddressModel):
    class Meta:
        abstract = True

    # Information about the recipient
    name = models.CharField(
        "Full name",
        max_length=settings.NAME_LENGTH
    )
    email = models.EmailField("Email address")
    phone_number = models.CharField(
        "Phone number",
        help_text="Use the format 555-555-5555",
        max_length=settings.PHONE_NUMBER_LENGTH,
    )
    can_receive_texts = models.BooleanField(
        "Can receive texts",
        help_text="Can the phone number provided receive text messages?",
    )
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
    notes = models.TextField(
        "Additional information",
        help_text="Is there anything else we should know about you or the person you are requesting support for that will help us complete the request better?",
        blank=True,
    )

    # Information about the request itself
    num_adults = models.PositiveSmallIntegerField("Number of adults in the household")
    num_children = models.PositiveSmallIntegerField("Number of children in the household")
    children_ages = models.CharField(
        "Ages of children",
        help_text="When able, we will try to provide additional snacks for children. If this is something you would be interested in, please list the ages of any children in the household so we may try to provide appropriate snacks for their age group.",
        max_length=settings.DEFAULT_LENGTH,
        blank=True,
    )
    food_allergies = models.TextField(
        "Food allergies",
        help_text="Please list any allergies or dietary restrictions",
        blank=True,
    )

    # Information about community status
    bipoc = models.BooleanField("Black, Indigenous, and People of Colour (BIPOC)")
    lgbtq = models.BooleanField("Lesbian, Gay, Bisexual, Trans, Queer (LGBTQ), gender non-conforming or non-binary")
    has_disability = models.BooleanField("Living with disabilities")
    immigrant_or_refugee = models.BooleanField("Newly arrived immigrant or refugee")
    housing_issues = models.BooleanField("Precariously housed (no fixed address, living in a shelter, etc.)")
    sex_worker = models.BooleanField("Sex worker")
    single_parent = models.BooleanField("Single parent")

    # Information about the delivery
    can_meet_for_delivery = models.BooleanField(
        "Able to meet delivery driver",
        help_text="We care about safety. Thus, we try to avoid delivery volunteers going into buildings or houses. Would you / the person requiring support be able to meet the delivery person in the lobby or door of the residence?",
    )
    delivery_details = models.TextField(
        "Delivery details",
        help_text="Please provide us with any details we may need to know for the delivery",
        blank=True,
    )
    availability = models.TextField(
        "Availability",
        help_text="Please list the days and times that you're available to receive a delivery",
    )

    # Information about the requester
    # Will be null if on_behalf_of is False, indicating request was by the recipient
    on_behalf_of = models.BooleanField(
        "On someone's behalf",
        help_text="Are you filling out this form on behalf of someone else?",
    )
    recipient_notified = models.BooleanField(
        "Recipient has been notified",
        help_text="Has the person you're filling out the form for been informed they will get a delivery?",
    )
    requester_name = models.CharField(
        "Your full name",
        max_length=settings.NAME_LENGTH,
        blank=True,
    )
    requester_email = models.EmailField(
        "Your email address",
        blank=True,
    )
    requester_phone_number = models.CharField(
        "Your phone number",
        help_text="Use the format 555-555-5555",
        max_length=settings.PHONE_NUMBER_LENGTH,
        blank=True,
    )

    # Legal
    accept_terms = models.BooleanField("Accept terms")

    # Admin
    delivery_date = models.DateField(blank=True, null=True)

    # System
    uuid = models.UUIDField(default=uuid.uuid4, editable=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    anonymized_latitude = models.FloatField(default=43.651070)  # default: Toronto latitude
    anonymized_longitude = models.FloatField(default=-79.347015)  # default: Toronto longitude

    def get_absolute_url(self):
        return reverse_lazy('recipients:request_detail', args=[str(self.id)])

    def send_confirmation_email(self):
        send_mail(
            "Confirming your The People's Pantry request",
            dedent(f"""
                Hi {self.name},
                Just confirming that we received your request for The People's Pantry.
                Your request ID is {self.uuid}
            """),
            None,  # From email (by setting None, it will use DEFAULT_FROM_EMAIL)
            [self.email]
        )

    def __str__(self):
        delivery_date = self.delivery_date.strftime("%m/%d/%Y") if self.delivery_date else "Unscheduled"
        return "[%s] %s for %s in %s for %d adult(s) and %d kid(s)" % (
            delivery_date, self._meta.verbose_name.capitalize(), self.name, self.city, self.num_adults, self.num_children,
        )



class MealRequest(HelpRequest):
    dairy_free = models.BooleanField("Dairy free")
    gluten_free = models.BooleanField("Gluten free")
    halal = models.BooleanField("Halal")
    low_carb = models.BooleanField("Low Carbohydrate")
    vegan = models.BooleanField("Vegan")
    vegetarian = models.BooleanField("Vegetarian")
    food_preferences = models.TextField(
        "Food preferences",
        help_text="Please list any food preferences (eg. meat, pasta, veggies, etc.)",
        blank=True,
    )
    will_accept_vegan = models.BooleanField(
        "Will accept vegan",
        help_text="Are you willing to accept a vegan meal even if you are not vegan?",
        default=True,
    )
    will_accept_vegetarian = models.BooleanField(
        "Will accept vegetarian",
        help_text="Are you willing to accept a vegetarian meal even if you are not vegetarian?",
        default=True,
    )


class GroceryRequest(HelpRequest):
    vegetables = models.CharField(
        "Vegetables",
        help_text="Select all that you want",
        max_length=settings.DEFAULT_LENGTH,
    )
    fruits = models.CharField(
        "Fruits",
        help_text="Select all that you want",
        max_length=settings.DEFAULT_LENGTH,
    )
    protein = models.CharField(
        "Protein",
        help_text="Select one of the following",
        choices=Protein.choices,
        max_length=settings.DEFAULT_LENGTH,
    )
    grains = models.CharField(
        "Grains",
        help_text="Select up to 3",
        max_length=settings.DEFAULT_LENGTH,
    )
    condiments = models.CharField(
        "Condiments",
        help_text="Select all that you want",
        max_length=settings.DEFAULT_LENGTH,
    )
    dairy = models.CharField(
        "Dairy",
        help_text="Select one of the following",
        choices=Dairy.choices,
        max_length=settings.DEFAULT_LENGTH,
    )
    baked_goods = models.BooleanField(
        "Baked goods",
        help_text="Sometimes we have baked goods to offer in our bundles, would you want baked goods?"
    )
    kid_snacks = models.BooleanField(
        "Kid snacks",
        help_text="Sometimes we have kid snacks to offer in our bundles, would you want kids' snacks?"
    )
    hygiene_products = models.CharField(
        "Hygiene products",
        help_text="Sometimes we are able to include personal hygiene products in our bundles, what personal hygiene products would you want? For example: sanitary pads, shampoo, etc.",
        max_length=settings.LONG_TEXT_LENGTH,
        blank=True,
    )


class Status(models.TextChoices):
    UNCONFIRMED = 'Unconfirmed', 'Unconfirmed'
    CHEF_ASSIGNED = 'Chef Assigned', 'Chef Assigned'
    DATE_CONFIRMED = 'Delivery Date Confirmed', 'Delivery Date Confirmed'
    DRIVER_ASSIGNED = 'Driver Assigned', 'Driver Assigned'
    RESCHEDULED = 'Recipient Rescheduled', 'Recipient Rescheduled'
    DELIVERED = 'Delivered', 'Delivered'


class UpdateNote(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        blank=True
    )
    request_id = models.ForeignKey(MealRequest, on_delete=models.CASCADE)
    note = models.CharField(max_length=settings.LONG_TEXT_LENGTH)

    # System
    uuid = models.UUIDField(default=uuid.uuid4, editable=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Delivery(models.Model):
    class Meta:
        verbose_name_plural = 'deliveries'

    chef = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        related_name="assigned_chef"
    )
    deliverer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        related_name="assigned_deliverer",
        null=True
    )
    request = models.ForeignKey(MealRequest, on_delete = models.CASCADE)
    status = models.CharField(
        "Status",
        max_length=settings.DEFAULT_LENGTH,
        choices=Status.choices,
        default=Status.UNCONFIRMED
    )
    pickup_start = models.TimeField(null=True)
    pickup_end = models.TimeField(null=True)
    dropoff_start = models.TimeField(null=True)
    dropoff_end = models.TimeField(null=True)
    container_delivery = models.BooleanField(default=False)

    # System
    uuid = models.UUIDField(default=uuid.uuid4, editable=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def delivery_date(self):
        if self.container_delivery:
            return self.request.delivery_date - datetime.timedelta(days=2)

        return self.request.delivery_date

    @property
    def container_provided(self):
        return Delivery.objects.filter(request=self.request, container_delivery=True).exists()

    def __str__(self):
        # delivery_date = self.delivery_date.strftime("%m/%d/%Y") if self.delivery_date else "Unscheduled"
        return "[%s] Delivering %s to %s for %s" % (
            self.status.capitalize(), self.request._meta.verbose_name.capitalize(), self.request.city, self.request.name,
        )
