import logging
from textwrap import dedent
from datetime import timedelta, time, date
from django.db import models
from django.conf import settings
from django.forms import model_to_dict
from django.core.exceptions import ValidationError
from django.utils import timezone
import pytz

from website.maps import GroceryDeliveryArea
from website.mail import custom_send_mail
from website.texts import TextMessage
from core.models import get_sentinel_user, ContactMixin, AddressMixin, DemographicMixin, TimestampsMixin, TelephoneField


logger = logging.getLogger(__name__)


class SendNotificationException(Exception):
    def __init__(self, message: str):
        self.message = message


class Status(models.TextChoices):
    UNCONFIRMED = 'Unconfirmed', 'Unconfirmed'
    CHEF_ASSIGNED = 'Chef Assigned', 'Chef Assigned'
    DRIVER_ASSIGNED = 'Driver Assigned', 'Driver Assigned'
    DATE_CONFIRMED = 'Delivery Date Confirmed', 'Delivery Date Confirmed'
    DELIVERED = 'Delivered', 'Delivered'


class MealRequestQuerySet(models.QuerySet):
    def delivered(self):
        return self.filter(status=Status.DELIVERED)

    def not_delivered(self):
        return self.exclude(status=Status.DELIVERED)


class MealRequest(DemographicMixin, ContactMixin, AddressMixin, TimestampsMixin, models.Model):
    objects = MealRequestQuerySet.as_manager()

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
        default=Status.UNCONFIRMED
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

    @classmethod
    def requests_paused(cls):
        """Are requests currently paused?"""
        return cls.requests_paused_by_limit() or cls.requests_paused_by_period()

    @classmethod
    def requests_paused_by_period(cls):
        if settings.DISABLE_MEALS_PERIOD:
            return False

        return not cls.within_signup_period()

    @classmethod
    def requests_paused_by_limit(cls):
        if settings.DISABLE_MEALS_LIMIT:
            return False

        return cls.active_requests() >= settings.MEALS_LIMIT

    @classmethod
    def within_signup_period(cls):
        now = timezone.now().astimezone(pytz.timezone('America/Toronto'))
        is_sunday = now.strftime('%A') == 'Sunday'
        is_after_noon = now.hour >= 12
        return is_sunday and is_after_noon

    @classmethod
    def active_requests(cls):
        return cls.objects.exclude(status__in=(Status.DATE_CONFIRMED, Status.DELIVERED)).count()

    @classmethod
    def has_open_request(cls, phone: str):
        """Does the user with the given phone number already have open requests?"""
        return cls.objects.filter(
            phone_number=phone
        ).exclude(
            status__in=(Status.DATE_CONFIRMED, Status.DELIVERED)
        ).exists()

    @property
    def stale(self):
        return (timezone.now() - self.created_at).days >= 7

    @property
    def delivered(self):
        return self.status == Status.DELIVERED

    def copy(self):
        """Clone the request with special business logic
        - The chef should remain the same but not the delivery driver
        - The date should be on the same day of the week, starting today or later
        - If the original date is None, so is the new date
        - Status should be Chef Assigned
        """
        kwargs = model_to_dict(self, exclude=[
            'id',
            'chef',
            'deliverer',
            'delivery_date',
            'status',
        ])

        new_date = self.delivery_date
        today = date.today()
        if new_date:
            while new_date <= today:
                new_date += timedelta(days=7)

        return MealRequest.objects.create(
            **kwargs,
            chef=self.chef,
            deliverer=None,
            delivery_date=new_date,
            status=Status.CHEF_ASSIGNED,
        )

    def send_confirmation_email(self):
        custom_send_mail(
            "Confirming your The People's Pantry request",
            dedent(f"""
                Hi {self.name},
                Just confirming that we received your request for The People's Pantry.
                Your request ID is {self.id}

                We depend on volunteers to sign up for our deliveries, and so your delivery will be scheduled once a chef and delivery volunteer sign up for your request (typically within 7-14 days). You will hear from us to confirm your delivery date once volunteers sign up. Thank you!
            """).strip(),
            [self.email],
            reply_to=settings.REQUEST_COORDINATORS_EMAIL
        )

    def send_recipient_meal_notification(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException("Recipient cannot receive text messages at their phone number")

        text = TextMessage(
            template="texts/meals/recipient/notification.txt",
            context={"request": self},
            api=api,
        )
        text.send(self.phone_number)
        self.comments.create(comment=f"Sent a text to recipient: {text.message}")

    def send_recipient_reminder_notification(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException("Recipient cannot receive text messages at their phone number")
        if not (self.dropoff_start and self.dropoff_end):
            raise SendNotificationException("Delivery does not have a dropoff time range scheduled")
        if self.deliverer is None:
            raise SendNotificationException("Delivery does not have a deliverer assigned")

        text = TextMessage(
            template="texts/meals/recipient/reminder.txt",
            context={"request": self},
            api=api,
        )
        text.send(self.phone_number)
        self.comments.create(comment=f"Sent a text to recipient: {text.message}")

    def send_recipient_delivery_notification(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException("Recipient cannot receive text messages at their phone number")
        if not (self.dropoff_start and self.dropoff_end):
            raise SendNotificationException("Delivery does not have a dropoff time range scheduled")
        if self.deliverer is None:
            raise SendNotificationException("Delivery does not have a deliverer assigned")

        text = TextMessage(
            template="texts/meals/recipient/delivery.txt",
            context={"request": self},
            api=api,
        )
        text.send(self.phone_number)
        self.comments.create(comment=f"Sent a text to recipient: {text.message}")

    def send_recipient_feedback_request(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException("Recipient cannot receive text messages at their phone number")

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
            raise SendNotificationException("Delivery does not have a pickup time range scheduled")

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
            raise SendNotificationException("Delivery does not have a pickup time range scheduled")
        if not (self.dropoff_start and self.dropoff_end):
            raise SendNotificationException("Delivery does not have a dropoff time range scheduled")

        text = TextMessage(
            template="texts/meals/deliverer/details.txt",
            context={"request": self},
            api=api,
        )
        text.send(self.deliverer.volunteer.phone_number)
        self.comments.create(comment=f"Sent a text to the deliverer: {text.message}")

    def __str__(self):
        return "Request #%d (%s): %d adult(s) and %d kid(s) in %s " % (
            self.id, self.name, self.num_adults, self.num_children, self.city,
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
    subject = models.ForeignKey(MealRequest, related_name="comments", on_delete=models.CASCADE)


class GiftCard(models.TextChoices):
    WALMART = 'Walmart', 'Walmart (Digital)'
    PRESIDENTS_CHOICE = "President's Choice", "President's Choice (Physical)"


class GroceryRequest(DemographicMixin, ContactMixin, AddressMixin, TimestampsMixin, models.Model):
    can_receive_texts = models.BooleanField(
        "Can receive texts",
        help_text="Can the phone number provided receive text messages?",
    )
    notes = models.TextField(
        "Additional information",
        help_text="Is there anything else we should know about you or the person you are requesting support for that will help us complete the request better?",
        blank=True,
    )
    gift_card = models.CharField(
        "Gift card",
        help_text="We offer both physical (mailed to you) and digital (emailed to you) gift cards. What type of gift card would you want?",
        max_length=settings.DEFAULT_LENGTH,
        choices=GiftCard.choices,
    )

    # Information about the request itself
    num_adults = models.PositiveSmallIntegerField(
        "Number of adults and teenagers in the household",
        help_text="Adults/teenagers 13 years of age and above",
    )
    num_children = models.PositiveSmallIntegerField(
        "Number of children in the household",
        help_text="Children under the age of 13"
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
    completed = models.BooleanField(
        "Completed",
        help_text="Has this request been completed?",
        default=False
    )

    def clean(self, *args, **kwargs):
        latitude, longitude = self.fetched_coordinates
        if not GroceryDeliveryArea.singleton().includes(longitude, latitude):
            logger.warning("Address outside of delivery area", extra={'address': self.address, 'coordinates': self.fetched_coordinates})
            raise ValidationError("Sorry, we don't currently offer grocery delivery in your area")

    @classmethod
    def requests_paused(cls):
        """Are requests currently paused?"""
        return cls.requests_paused_by_limit() or cls.requests_paused_by_period()

    @classmethod
    def requests_paused_by_period(cls):
        if settings.DISABLE_GROCERIES_PERIOD:
            return False

        return not cls.within_signup_period()

    @classmethod
    def requests_paused_by_limit(cls):
        if settings.DISABLE_GROCERIES_LIMIT:
            return False

        return cls.active_box_requests() >= settings.GROCERIES_LIMIT

    @classmethod
    def within_signup_period(cls):
        now = timezone.now().astimezone(pytz.timezone('America/Toronto'))
        is_sunday = now.strftime('%A') == 'Sunday'
        is_after_noon = now.hour >= 12
        return is_sunday and is_after_noon

    @classmethod
    def active_box_requests(cls):
        """Calculate the number of box requests that are currently "active"

        Requests are considered active if they don't have a delivery assigned, and aren't
        marked as completed. A request could potentially be marked complete but not have
        a delivery date as a way of cancelling it (if the organizers wanted to keep it) in
        the system for some reason, but not have it count towards the limit.

        A box request is not the same as a grocery request. Each grocery request specifies
        a number of adults and children and we use that information to calculate how many
        boxes they should receive.

        The formula is:
        - 1 box if there's less than 4 adults
        - 2 boxes if there's between (inclusive) 4 and 6 adults
        - 3 boxes if there's 7 or more adults

        We use Django's annotation/aggregation features to compute this value
        """
        active_requests = cls.objects.filter(delivery_date=None, completed=False)
        boxes = active_requests.annotate(
            boxes=models.Case(
                models.When(num_adults__lt=4, then=models.Value(1)),
                models.When(num_adults__lt=7, then=models.Value(2)),
                default=models.Value(3),
                output_field=models.IntegerField()
            )
        ).aggregate(
            total_boxes=models.Sum('boxes')
        )['total_boxes'] or 0

        return boxes

    @classmethod
    def has_open_request(cls, phone: str):
        """Does the user with the given phone number already have open requests?"""
        return cls.objects.filter(phone_number=phone, delivery_date=None, completed=False).exists()

    def send_confirmation_email(self):
        custom_send_mail(
            "Confirming your The People's Pantry request",
            dedent(f"""
                Hi {self.name},
                Just confirming that we received your request for The People's Pantry.
                Your request ID is G{self.id}

                Grocery deliveries take one week to process before arranging a delivery date. Your delivery will be scheduled for the week after next. You will hear from us in 7 days about the date your request is scheduled for.
            """).strip(),
            [self.email],
            reply_to=settings.REQUEST_COORDINATORS_EMAIL
        )

    def send_recipient_scheduled_notification(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException("Recipient cannot receive text messages at their phone number")
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
            raise SendNotificationException("Recipient cannot receive text messages at their phone number")

        text = TextMessage(
            template="texts/groceries/allergy.txt",
            context={"request": self},
            group_name="groceries",
            api=api,
        )
        text.send(self.phone_number)
        self.comments.create(comment=f"Sent a text to recipient: {text.message}")

    def send_recipient_reminder_notification(self, api=None):
        if not self.can_receive_texts:
            raise SendNotificationException("Recipient cannot receive text messages at their phone number")

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
            raise SendNotificationException("Recipient cannot receive text messages at their phone number")

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
            raise SendNotificationException("Recipient cannot receive text messages at their phone number")
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
            self.id, self.name, self.num_adults, self.num_children, self.city,
        )


class GroceryRequestComment(CommentModel):
    subject = models.ForeignKey(GroceryRequest, related_name="comments", on_delete=models.CASCADE)
