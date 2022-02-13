import logging
from datetime import time
from django.db import models
from django.db.models import F
from django.db.models.functions import Power, Sqrt
from django.conf import settings
from django.forms import model_to_dict
from django.core.exceptions import ValidationError
from django.utils import timezone

from website.maps import GroceryDeliveryArea, Geocoder
from website.texts import TextMessage
from core.models import (
    get_sentinel_user,
    ContactMixin,
    TorontoAddressMixin,
    DemographicMixin,
    TimestampsMixin,
    TelephoneField,
)
from .emails import (
    MealRequestConfirmationEmail,
    GroceryRequestConfirmationEmail,
    MealRequestLotterySelectedEmail,
    MealRequestLotteryNotSelectedEmail,
)


logger = logging.getLogger(__name__)


class SendNotificationException(Exception):
    def __init__(self, message: str):
        self.message = message


class MealRequestQuerySet(models.QuerySet):
    def available_for_chef_signup(self):
        return self.filter(chef__isnull=True,).exclude(
            status__in=(MealRequest.Status.SUBMITTED, *MealRequest.COMPLETED_STATUSES),
        )

    def available_for_deliverer_signup(self):
        return (
            self.filter(
                deliverer__isnull=True,
            )
            .exclude(delivery_date__isnull=True)
            .exclude(
                status__in=(
                    MealRequest.Status.SUBMITTED,
                    *MealRequest.COMPLETED_STATUSES,
                ),
            )
        )

    def delivered(self):
        return self.filter(status=MealRequest.Status.DELIVERED)

    def not_delivered(self):
        return self.exclude(status=MealRequest.Status.DELIVERED)

    def with_delivery_distance(self, chef=None):
        """
        Calculates the distance between the recipient and the chef in kilometres
        A chef can optionally be provided, for cases like when a chef is signing up
        If no chef is provided, this assumes that one is signed up

        Calculates based on euclidean distance
        This isn't ideal for this format, but works fine over short distances
        """
        if chef is not None:
            chef_latitude, chef_longitude = chef.volunteer.coordinates
        else:
            chef_latitude = F("chef__volunteer__anonymized_latitude")
            chef_longitude = F("chef__volunteer__anonymized_longitude")

        latitude_distance = (
            F("anonymized_latitude") - chef_latitude
        ) * Geocoder.LATITUDE_DEGREE_LENGTH
        longitude_distance = (
            F("anonymized_longitude") - chef_longitude
        ) * Geocoder.LONGITUDE_DEGREE_LENGTH
        return self.annotate(
            delivery_distance=Sqrt(
                Power(latitude_distance, 2) + Power(longitude_distance, 2)
            )
        )


class MealRequest(
    DemographicMixin, ContactMixin, TorontoAddressMixin, TimestampsMixin, models.Model
):
    STALE_AFTER_DAYS = 7
    objects = MealRequestQuerySet.as_manager()

    class Status(models.TextChoices):
        SUBMITTED = "Submitted", "Submitted"
        SELECTED = "Unconfirmed", "Selected"  # Previously called UNCONFIRMED
        CHEF_ASSIGNED = "Chef Assigned", "Chef Assigned"
        DRIVER_ASSIGNED = "Driver Assigned", "Driver Assigned"
        DATE_CONFIRMED = "Delivery Date Confirmed", "Delivery Date Confirmed"
        DELIVERED = "Delivered", "Delivered"
        UNSUCCESSFUL = "Unsuccessful", "Unsuccessful"
        NOT_SELECTED = "Not Selected", "Not Selected"

    COMPLETED_STATUSES = (Status.DELIVERED, Status.UNSUCCESSFUL, Status.NOT_SELECTED)

    # Information about the recipient
    can_receive_texts = models.BooleanField(
        "Can receive texts",
        help_text="Can the phone number provided receive text messages?",
    )
    notes = models.TextField(
        "Additional information",
        help_text="Is there anything else we should know about you or the person you are requesting support for that will help us complete the request better?",
        blank=True,
    )

    # Information about the request itself
    num_adults = models.PositiveSmallIntegerField("Number of adults in the household")
    num_children = models.PositiveSmallIntegerField(
        "Number of children in the household"
    )
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

    # Information about the delivery
    can_meet_for_delivery = models.BooleanField(
        "Able to meet delivery driver",
        help_text="Please confirm that you / the person requiring support will be able to meet the delivery person in the lobby or door of the residence, while wearing protective equipment such as masks?",
        default=True,
    )
    delivery_details = models.TextField(
        "Delivery details",
        help_text="Please provide us with any details we may need to know for the delivery",
        blank=True,
    )
    availability = models.TextField(
        "Availability",
        help_text="Our deliveries will be done on Fridays, Saturdays and Sundays between 12 and 8 PM. Please list the days and times that you're available to receive a delivery",
    )
    covid = models.BooleanField(
        "COVID-19",
        help_text="Have you been diagnosed with, or are you currently experiencing any symptoms of COVID-19? Such as fever, cough, difficulty breathing, or chest pain?",
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
    requester_phone_number = TelephoneField(
        "Your phone number",
        blank=True,
    )

    dairy_free = models.BooleanField("Dairy free")
    gluten_free = models.BooleanField("Gluten free")
    halal = models.BooleanField("Halal")
    kosher = models.BooleanField("Kosher")
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

    # Legal
    accept_terms = models.BooleanField("Accept terms")

    # Delivery
    chef = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        related_name="cooked_meal_requests",
        null=True,
        blank=True,
    )
    deliverer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        related_name="delivered_meal_requests",
        null=True,
        blank=True,
    )
    status = models.CharField(
        "Status",
        max_length=settings.DEFAULT_LENGTH,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    pickup_details = models.TextField(
        "Pickup details",
        help_text="List any details the deliverer might need to know for pickup",
        blank=True,
    )
    delivery_date = models.DateField("Delivery date", null=True, blank=True)
    pickup_start = models.TimeField(default=time(12, 00))
    pickup_end = models.TimeField(default=time(17, 00))
    dropoff_start = models.TimeField(default=time(18, 00))
    dropoff_end = models.TimeField(default=time(20, 00))
    meal = models.TextField(
        "Meal",
        help_text="(Optional) Let us know what you plan on cooking!",
        blank=True,
    )
    containers = models.TextField(
        "Containers",
        help_text="Expected number and size of containers that you'll use to package this meal",
        blank=True,
    )

    @classmethod
    def requests_paused(cls):
        """Are requests currently paused?"""
        if settings.DISABLE_MEALS_PERIOD:
            return False
        return not cls.within_signup_period()

    @classmethod
    def within_signup_period(cls):
        """Requests are open from Friday at 9am until Sunday at 2pm"""
        now = timezone.localtime()
        weekday = now.strftime("%A")
        is_friday = weekday == "Friday"
        is_saturday = weekday == "Saturday"
        is_sunday = weekday == "Sunday"
        is_after_9am = now.hour >= 9
        is_before_2pm = now.hour < 14
        return (
            (is_friday and is_after_9am) or is_saturday or (is_sunday and is_before_2pm)
        )

    @classmethod
    def active_requests(cls):
        return cls.objects.exclude(
            status__in=(cls.Status.DATE_CONFIRMED, *cls.COMPLETED_STATUSES)
        ).count()

    @classmethod
    def has_open_request(cls, phone: str):
        """Does the user with the given phone number already have open requests?"""
        return (
            cls.objects.filter(phone_number=phone)
            .exclude(status__in=(cls.Status.DATE_CONFIRMED, *cls.COMPLETED_STATUSES))
            .exists()
        )

    @property
    def stale(self):
        return (timezone.now() - self.created_at).days >= self.STALE_AFTER_DAYS

    @property
    def delivered(self):
        return self.status == MealRequest.Status.DELIVERED

    def copy(self):
        """Clone the request and treat it like a new submission"""
        kwargs = model_to_dict(
            self,
            exclude=[
                "id",
                "chef",
                "deliverer",
                "delivery_date",
                "pickup_start",
                "pickup_end",
                "dropoff_start",
                "dropoff_end",
                "status",
            ],
        )
        return MealRequest.objects.create(**kwargs)

    def send_confirmation_email(self):
        return MealRequestConfirmationEmail().send(self.email, {"request": self})

    def send_lottery_selected_email(self):
        return MealRequestLotterySelectedEmail().send(self.email, {"request": self})

    def send_lottery_not_selected_email(self):
        return MealRequestLotteryNotSelectedEmail().send(self.email, {"request": self})

    def send_recipient_meal_notification(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException(
                "Recipient cannot receive text messages at their phone number"
            )

        text = TextMessage(
            template="texts/meals/recipient/notification.txt",
            context={"request": self},
            api=api,
        )
        text.send(self.phone_number)
        self.comments.create(comment=f"Sent a text to recipient: {text.message}")

    def send_recipient_reminder_notification(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException(
                "Recipient cannot receive text messages at their phone number"
            )
        if not (self.dropoff_start and self.dropoff_end):
            raise SendNotificationException(
                "Delivery does not have a dropoff time range scheduled"
            )
        if self.deliverer is None:
            raise SendNotificationException(
                "Delivery does not have a deliverer assigned"
            )

        text = TextMessage(
            template="texts/meals/recipient/reminder.txt",
            context={"request": self},
            api=api,
        )
        text.send(self.phone_number)
        self.comments.create(comment=f"Sent a text to recipient: {text.message}")

    def send_recipient_delivery_notification(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException(
                "Recipient cannot receive text messages at their phone number"
            )
        if not (self.dropoff_start and self.dropoff_end):
            raise SendNotificationException(
                "Delivery does not have a dropoff time range scheduled"
            )
        if self.deliverer is None:
            raise SendNotificationException(
                "Delivery does not have a deliverer assigned"
            )

        text = TextMessage(
            template="texts/meals/recipient/delivery.txt",
            context={"request": self},
            api=api,
        )
        text.send(self.phone_number)
        self.comments.create(comment=f"Sent a text to recipient: {text.message}")

    def send_recipient_feedback_request(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException(
                "Recipient cannot receive text messages at their phone number"
            )

        text = TextMessage(
            template="texts/meals/recipient/feedback.txt",
            context={"request": self},
            api=api,
        )
        text.send(self.phone_number)
        self.comments.create(comment=f"Sent a text to recipient: {text.message}")

    def send_chef_reminder_notification(self, api=None):
        if not self.chef:
            raise SendNotificationException("No chef assigned to this delivery")
        if not self.deliverer:
            raise SendNotificationException("No deliverer assigned to this delivery")
        if not (self.pickup_start and self.pickup_end):
            raise SendNotificationException(
                "Delivery does not have a pickup time range scheduled"
            )

        text = TextMessage(
            template="texts/meals/chef/reminder.txt",
            context={"request": self},
            api=api,
        )
        text.send(self.chef.volunteer.phone_number)
        self.comments.create(comment=f"Sent a text to the chef: {text.message}")

    def send_deliverer_reminder_notification(self, api=None):
        if not self.deliverer:
            raise SendNotificationException("No deliverer assigned to this delivery")

        text = TextMessage(
            template="texts/meals/deliverer/reminder.txt",
            context={"request": self},
            api=api,
        )
        text.send(self.deliverer.volunteer.phone_number)
        self.comments.create(comment=f"Sent a text to the deliverer: {text.message}")

    def send_detailed_deliverer_notification(self, api=None):
        """Send a detailed notification to the deliverer with content for the delivery"""
        if not self.deliverer:
            raise SendNotificationException("No deliverer assigned to this delivery")
        if not self.chef:
            raise SendNotificationException("No chef assigned to this delivery")
        if not self.delivery_date:
            raise SendNotificationException("Delivery does not have a date scheduled")
        if not (self.pickup_start and self.pickup_end):
            raise SendNotificationException(
                "Delivery does not have a pickup time range scheduled"
            )
        if not (self.dropoff_start and self.dropoff_end):
            raise SendNotificationException(
                "Delivery does not have a dropoff time range scheduled"
            )

        text = TextMessage(
            template="texts/meals/deliverer/details.txt",
            context={"request": self},
            api=api,
        )
        text.send(self.deliverer.volunteer.phone_number)
        self.comments.create(comment=f"Sent a text to the deliverer: {text.message}")

    def get_previous_requests(self):
        return self.__class__.objects.filter(
            phone_number=self.phone_number,
            created_at__lt=self.created_at,
        ).order_by("-created_at")

    def count_consecutive_previously_unselected(self):
        """How many times did the same recipient consecutively submit and get NOT_SELECTED?"""
        count = 0
        for request in self.get_previous_requests():
            if request.status == MealRequest.Status.NOT_SELECTED:
                count += 1
            else:
                break
        return count

    def get_lottery_weight(self):
        weight = 1
        weight += self.count_consecutive_previously_unselected()
        if self.in_any_demographic():
            weight += 1
        return weight

    def __str__(self):
        return "Request #%d (%s): %d adult(s) and %d kid(s) in %s " % (
            self.id,
            self.name,
            self.num_adults,
            self.num_children,
            self.city,
        )


class CommentModel(models.Model):
    class Meta:
        abstract = True

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        null=True,
        blank=True,
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def display_comment(self):
        """Render a truncated version of the comment"""
        max_length = 50
        if self.comment is None:
            return self.comment
        if len(self.comment) < max_length:
            return self.comment
        return f"{self.comment[:max_length]}..."

    def __str__(self):
        author = self.author or "System"
        created_at = self.created_at.astimezone(timezone.get_current_timezone())
        return f"[{created_at:%Y-%m-%d %I:%M:%S %p}] {author}: {self.display_comment}"


class MealRequestComment(CommentModel):
    subject = models.ForeignKey(
        MealRequest, related_name="comments", on_delete=models.CASCADE
    )


class GroceryRequest(
    DemographicMixin, ContactMixin, TorontoAddressMixin, TimestampsMixin, models.Model
):
    class Status(models.TextChoices):
        SUBMITTED = "Submitted", "Submitted"
        SELECTED = "Selected", "Selected"
        DELIVERED = "Delivered", "Delivered"
        UNSUCCESSFUL = "Unsuccessful", "Unsuccessful"
        NOT_SELECTED = "Not Selected", "Not Selected"

    COMPLETED_STATUSES = (Status.DELIVERED, Status.UNSUCCESSFUL, Status.NOT_SELECTED)

    can_receive_texts = models.BooleanField(
        "Can receive texts",
        help_text="Can the phone number provided receive text messages?",
    )
    notes = models.TextField(
        "Additional information",
        help_text="Is there anything else we should know about you or the person you are requesting support for that will help us complete the request better?",
        blank=True,
    )

    # Information about the request itself
    num_adults = models.PositiveSmallIntegerField(
        "Number of adults and teenagers in the household",
        help_text="Adults/teenagers 13 years of age and above",
    )
    num_children = models.PositiveSmallIntegerField(
        "Number of children in the household", help_text="Children under the age of 13"
    )
    children_ages = models.CharField(
        "Ages of children",
        help_text="When able, we will try to provide additional snacks for children. If this is something you would be interested in, please list the ages of any children in the household so we may try to provide appropriate snacks for their age group.",
        max_length=settings.DEFAULT_LENGTH,
        blank=True,
    )
    food_allergies = models.TextField(
        "Food allergies",
        help_text="Because of logistics constraints, we are unable to assemble boxes according to your needs. If you have an allergy to a food item that is included in the produce box, we won’t be able to send you the box.",
        blank=True,
    )

    # Information about the delivery
    buzzer = models.CharField(
        "Buzzer code",
        help_text="Does your building requires a buzzer code for us to contact you?",
        blank=True,
        max_length=settings.DEFAULT_LENGTH,
    )
    delivery_details = models.TextField(
        "Delivery details",
        help_text="Please provide us with any details we may need to know for the delivery",
        blank=True,
    )
    covid = models.BooleanField(
        "COVID-19",
        help_text="Have you been diagnosed with, or are you currently experiencing any symptoms of COVID-19? Such as fever, cough, difficulty breathing, or chest pain?",
    )
    delivery_date = models.DateField("Delivery date", null=True, blank=True)

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
    requester_phone_number = TelephoneField(
        "Your phone number",
        blank=True,
    )

    # Legal
    accept_terms = models.BooleanField("Accept terms")

    # System
    status = models.CharField(
        "Status",
        max_length=settings.DEFAULT_LENGTH,
        choices=Status.choices,
        default=Status.SELECTED,
    )

    def clean(self, *args, **kwargs):
        latitude, longitude = self.fetched_coordinates
        if not GroceryDeliveryArea.singleton().includes(longitude, latitude):
            logger.warning(
                "Address outside of delivery area",
                extra={
                    "address": self.address,
                    "coordinates": self.fetched_coordinates,
                },
            )
            raise ValidationError(
                "Sorry, we don't currently offer grocery delivery in your area"
            )

    @classmethod
    def requests_paused(cls):
        """Are requests currently paused?"""
        if settings.DISABLE_GROCERIES:
            return True
        if settings.DISABLE_GROCERIES_PERIOD:
            return False
        return not cls.within_signup_period()

    @classmethod
    def within_signup_period(cls):
        """Requests are open from Friday at 9am until Sunday at 2pm"""
        now = timezone.localtime()
        weekday = now.strftime("%A")
        is_friday = weekday == "Friday"
        is_saturday = weekday == "Saturday"
        is_sunday = weekday == "Sunday"
        is_after_9am = now.hour >= 9
        is_before_2pm = now.hour < 14
        return (
            (is_friday and is_after_9am) or is_saturday or (is_sunday and is_before_2pm)
        )

    @classmethod
    def has_open_request(cls, phone: str):
        """Does the user with the given phone number already have open requests?"""
        return (
            cls.objects.filter(
                phone_number=phone,
                delivery_date=None,
            )
            .exclude(status__in=cls.COMPLETED_STATUSES)
            .exists()
        )

    @property
    def boxes(self):
        if self.num_adults < 4:
            return 1
        elif self.num_adults < 7:
            return 2
        else:
            return 3

    def copy(self):
        """Clone the request and treat it like a new submission"""
        kwargs = model_to_dict(self, exclude=["id", "delivery_date", "status"])
        return GroceryRequest.objects.create(**kwargs)

    def send_confirmation_email(self):
        return GroceryRequestConfirmationEmail().send(self.email, {"request": self})

    def send_recipient_scheduled_notification(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException(
                "Recipient cannot receive text messages at their phone number"
            )
        if not (self.delivery_date):
            raise SendNotificationException("Delivery date is not specified")

        text = TextMessage(
            template="texts/groceries/scheduled.txt",
            context={"request": self},
            group_name="groceries",
            api=api,
        )
        text.send(self.phone_number)
        self.comments.create(comment=f"Sent a text to recipient: {text.message}")

    def send_recipient_allergy_notification(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException(
                "Recipient cannot receive text messages at their phone number"
            )

        text = TextMessage(
            template="texts/groceries/allergy.txt",
            context={"request": self},
            group_name="groceries",
            api=api,
        )
        text.send(self.phone_number)
        self.comments.create(comment=f"Sent a text to recipient: {text.message}")

    def send_recipient_notice_notification(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException(
                "Recipient cannot receive text messages at their phone number"
            )

        text = TextMessage(
            template="texts/groceries/notice.txt",
            context={"request": self},
            group_name="groceries",
            api=api,
        )
        text.send(self.phone_number)
        self.comments.create(comment=f"Sent a text to recipient: {text.message}")

    def send_recipient_reminder_notification(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException(
                "Recipient cannot receive text messages at their phone number"
            )

        text = TextMessage(
            template="texts/groceries/reminder.txt",
            context={"request": self},
            group_name="groceries",
            api=api,
        )
        text.send(self.phone_number)
        self.comments.create(comment=f"Sent a text to recipient: {text.message}")

    def send_recipient_rescheduled_notification(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException(
                "Recipient cannot receive text messages at their phone number"
            )

        text = TextMessage(
            template="texts/groceries/rescheduled.txt",
            context={"request": self},
            group_name="groceries",
            api=api,
        )
        text.send(self.phone_number)
        self.comments.create(comment=f"Sent a text to recipient: {text.message}")

    def send_recipient_confirm_received_notification(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException(
                "Recipient cannot receive text messages at their phone number"
            )
        if not (self.delivery_date):
            raise SendNotificationException("Delivery date is not specified")

        text = TextMessage(
            template="texts/groceries/confirmation.txt",
            context={"request": self},
            group_name="groceries",
            api=api,
        )
        text.send(self.phone_number)
        self.comments.create(comment=f"Sent a text to recipient: {text.message}")

    def __str__(self):
        return "Request #G%d (%s): %d adult(s) and %d kid(s) in %s " % (
            self.id,
            self.name,
            self.num_adults,
            self.num_children,
            self.city,
        )


class GroceryRequestComment(CommentModel):
    subject = models.ForeignKey(
        GroceryRequest, related_name="comments", on_delete=models.CASCADE
    )
