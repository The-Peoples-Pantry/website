import uuid
from django.db import models
from django.conf import settings
from django.urls import reverse_lazy
from django.contrib import admin

from core.models import get_sentinel_user

class Cities(models.TextChoices):
    AJAX = 'Ajax', 'Ajax'
    AURORA = 'Aurora', 'Aurora'
    BRAMPTON = 'Brampton', 'Brampton'
    BROCK = 'Brock', 'Brock'
    BURLINGTON = 'Burlington', 'Burlington'
    CALEDON = 'Caledon', 'Caledon'
    CLARINGTON = 'Clarington', 'Clarington'
    EAST_GWILIMBURY = 'East Gwilimbury', 'East Gwilimbury'
    EAST_YORK = 'East York', 'East York'
    ETOBICOKE = 'Etobicoke', 'Etobicoke'
    GEORGINA = 'Georgina', 'Georgina'
    HALTON_HILLS = 'Halton Hills', 'Halton Hills'
    HAMILTON = 'Hamilton', 'Hamilton'
    KING = 'King', 'King'
    MAPLE = 'Maple', 'Maple'
    MARKHAM = 'Markham', 'Markham'
    MILTON = 'Milton', 'Milton'
    MISSISSAUGA = 'Mississauga', 'Mississauga'
    NEWMARKET = 'Newmarket', 'Newmarket'
    NORTH_YORK = 'North York', 'North York'
    OAKVILLE = 'Oakville', 'Oakville'
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


class Days(models.TextChoices):
    MONDAY = 'MONDAY'
    TUESDAY = 'TUESDAY'
    WEDNESDAY = 'WEDNESDAY'
    THURSDAY = 'THURSDAY'
    FRIDAY = 'FRIDAY'
    SATURDAY = 'SATURDAY'
    SUNDAY = 'SUNDAY'


class TimePeriods(models.TextChoices):
    PERIOD_12_14 = '12 - 2 PM', '12 - 2 PM'
    PERIOD_14_16 = '2 - 4 PM', '2 - 4 PM'
    PERIOD_16_18 = '4 - 6 PM', '4 - 6 PM'
    PERIOD_16_20 = '6 - 8 PM', '6 - 8 PM'
    PERIOD_20_22 = '8 - 10 PM', '8 - 10 PM'


class MealRequest(models.Model):
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

    # Information about community status
    bipoc = models.BooleanField("Black, Indigenous, and People of Colour (BIPOC)")
    lgbtq = models.BooleanField("Lesbian, Gay, Bisexual, Trans, Queer (LGBTQ), gender non-conforming or non-binary")
    has_disability = models.BooleanField("Living with disabilities")
    immigrant_or_refugee = models.BooleanField("Newly arrived immigrant or refugee")
    housing_issues = models.BooleanField("Precariously housed (no fixed address, living in a shelter, etc.)")
    sex_worker = models.BooleanField("Sex worker")
    single_parent = models.BooleanField("Single parent")

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
    available_days = models.CharField(
        "Available days",
        help_text="What days are you (or the person you're requesting for) available for receiving the delivery?",
        max_length=settings.DEFAULT_LENGTH,
    )
    available_time_periods = models.CharField(
        "Available time periods",
        help_text="What times are you (or the person you're requesting for) available for receiving the delivery?",
        max_length=settings.DEFAULT_LENGTH,
    )

    # Dietary restrictions
    dairy_free = models.BooleanField("Dairy free")
    gluten_free = models.BooleanField("Gluten free")
    halal = models.BooleanField("Halal")
    low_carb = models.BooleanField("Low Carbohydrate")
    vegan = models.BooleanField("Vegan")
    vegetarian = models.BooleanField("Vegetarian")

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


class MealRequestAdmin(admin.ModelAdmin):
    readonly_fields = ('uuid',)


class Status(models.TextChoices):
    UNCONFIRMED = 'Unconfirmed', 'Unconfirmed'
    CHEF_ASSIGNED = 'Chef Assigned', 'Chef Assigned'
    SCHEDULED = 'Scheduled for Delivery', 'Scheduled for Delivery'
    CONFIRMED = 'Delivery Confirmed', 'Delivery Confirmed'
    RESCHEDULED = 'Rescheduled', 'Rescheduled'
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


class UpdateNoteAdmin(admin.ModelAdmin):
    readonly_fields = ('uuid',)

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
    dropoff_start = models.TimeField(null=True)
    container_delivery = models.BooleanField(default=False)

    # System
    uuid = models.UUIDField(default=uuid.uuid4, editable=True)
    created_at = models.DateTimeField(auto_now_add=True)

class DeliveryAdmin(admin.ModelAdmin):
    readonly_fields = ('uuid',)
