import logging
from textwrap import dedent
from datetime import datetime, timedelta
import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.utils import timezone
import pytz

from website.mail import custom_send_mail
from website.text_messaging import send_text
from core.models import get_sentinel_user, ContactInfo, GroceryPickupAddress


logger = logging.getLogger(__name__)


class SendNotificationException(Exception):
    def __init__(self, message: str):
        self.message = message


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


class HelpRequest(ContactInfo):
    class Meta:
        abstract = True

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

    # System
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def stale(self):
        return (timezone.now() - self.created_at).days >= 7

    def get_absolute_url(self):
        return reverse_lazy('recipients:request_detail', args=[str(self.id)])

    def send_confirmation_email(self):
        custom_send_mail(
            "Confirming your The People's Pantry request",
            dedent(f"""
                Hi {self.name},
                Just confirming that we received your request for The People's Pantry.
                Your request ID is {self.id}
            """),
            [self.email],
            reply_to=settings.REQUEST_COORDINATORS_EMAIL
        )

    def __str__(self):
        return "Request #%d (%s): %d adult(s) and %d kid(s) in %s " % (
            self.id, self.name, self.num_adults, self.num_children, self.city,
        )


class MealRequest(HelpRequest):
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

    @classmethod
    def requests_paused(cls):
        """Are requests currently paused?"""
        return cls.active_requests() >= settings.PAUSE_MEALS or not cls.within_signup_period()

    @classmethod
    def within_signup_period(cls):
        now = timezone.now().astimezone(pytz.timezone('America/Toronto'))
        is_saturday = now.strftime('%A') == 'Saturday'
        is_after_ten_am = now.hour >= 10
        return is_saturday and is_after_ten_am

    @classmethod
    def active_requests(cls):
        return cls.objects.exclude(
            delivery__status__in=(Status.DATE_CONFIRMED, Status.DELIVERED)
        ).count()

    @classmethod
    def has_open_request(cls, phone: str):
        """Does the user with the given email already have open requests?"""
        return cls.objects.filter(
            phone_number=phone
        ).exclude(
            delivery__status__in=(Status.DATE_CONFIRMED, Status.DELIVERED)
        ).exists()


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
        null=True,
        blank=True,
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

    @classmethod
    def requests_paused(cls):
        """Are requests currently paused?"""
        # TODO: Update this to exclude completed grocery deliveries once we have GroceryDelivery
        active_requests = cls.objects.count()
        return active_requests >= settings.PAUSE_GROCERIES


class Status(models.TextChoices):
    UNCONFIRMED = 'Unconfirmed', 'Unconfirmed'
    CHEF_ASSIGNED = 'Chef Assigned', 'Chef Assigned'
    DRIVER_ASSIGNED = 'Driver Assigned', 'Driver Assigned'
    DATE_CONFIRMED = 'Delivery Date Confirmed', 'Delivery Date Confirmed'
    RESCHEDULED = 'Recipient Rescheduled', 'Recipient Rescheduled'
    DELIVERED = 'Delivered', 'Delivered'


class BaseDelivery(models.Model):
    class Meta:
        abstract = True

    status = models.CharField(
        "Status",
        max_length=settings.DEFAULT_LENGTH,
        choices=Status.choices,
        default=Status.UNCONFIRMED
    )
    date = models.DateField("Delivery date", null=True, blank=True)
    pickup_start = models.TimeField(null=True, blank=True)
    pickup_end = models.TimeField(null=True, blank=True)
    dropoff_start = models.TimeField(null=True, blank=True)
    dropoff_end = models.TimeField(null=True, blank=True)

    def clean(self, *args, **kwargs):
        super(BaseDelivery, self).clean(*args, **kwargs)
        if self.pickup_end and self.pickup_start and self.pickup_end <= self.pickup_start:
            raise ValidationError("The pickup end time must be after the pickup start time")
        if self.dropoff_end and self.dropoff_start and self.dropoff_end <= self.dropoff_start:
            raise ValidationError("The dropoff end time must be after the dropoff start time")
        if self.dropoff_start and self.pickup_start and self.dropoff_start <= self.pickup_start:
            raise ValidationError("The dropoff start time must be after the pickup start time")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(BaseDelivery, self).save(*args, **kwargs)

    # System
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)


class GroceryDelivery(BaseDelivery):
    class Meta:
        verbose_name_plural = 'grocery deliveries'

    request = models.OneToOneField(
        GroceryRequest,
        on_delete=models.CASCADE,
        related_name='delivery',
    )
    deliverer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        related_name="delivered_grocery_deliveries",
        null=True,
        blank=True,
    )
    pickup_address = models.ForeignKey(
        GroceryPickupAddress,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def send_recipient_delivery_notification(self):
        """Send a follow-up notification to a recipient, lets them know that a delivery driver will drop if off within a certain time window"""
        # Perform validation first that we _can_ send this notification
        if not self.request.can_receive_texts:
            raise SendNotificationException("Recipient cannot receive text messages at their phone number")

        if not (self.dropoff_start and self.dropoff_end):
            raise SendNotificationException("Delivery does not have a dropoff time range scheduled")

        # Date is in the format "Weekday Month Year" eg. Sunday November 29
        # Time is in the format "Hour:Minute AM/PM" eg. 09:30 PM
        message = dedent(f"""
            Hi {self.request.name},
            This is a message from The People's Pantry.
            Your grocery bundle delivery is scheduled for {self.date:%A %B %d} between {self.dropoff_start:%I:%M %p} and {self.dropoff_end:%I:%M %p}.
            Since we depend on volunteers for our deliveries, sometimes we are not able to do all deliveries scheduled for the day. If that’s the case with your delivery, we will inform you by 6 PM on the day of the delivery and your delivery will be rescheduled for the following day.
            Please confirm you got this message and let us know if you can accept the delivery.
            Thank you!
        """)
        send_text(self.request.phone_number, message)
        self.comments.create(comment=f"Sent a text to recipient: {message}")
        logger.info("Sent recipient delivery notification text for Meal Request %d to %s", self.request.id, self.request.phone_number)

    def send_deliverer_reminder_notification(self):
        """Send a reminder notification to the deliverer"""
        if not self.deliverer:
            raise SendNotificationException("No deliverer assigned to this delivery")

        message = dedent(f"""
            Hi {self.deliverer.volunteer.name},
            This is a message from The People's Pantry.
            Just reminding you of the upcoming grocery bundle you're delivering on {self.date:%A %B %d} between {self.dropoff_start:%I:%M %p} and {self.dropoff_end:%I:%M %p}.
            Please confirm you got this message and let us know if you need any assistance.
            Thank you!
        """)
        send_text(self.deliverer.volunteer.phone_number, message)
        self.comments.create(comment=f"Sent a text to the deliverer: {message}")
        logger.info("Sent deliverer reminder notification text for Grocery bundle %d to %s", self.request.id, self.deliverer.volunteer.phone_number)

    def __str__(self):
        return "[%s] Delivering request id #%d (%s) to %s for %s" % (
            self.status.capitalize(), self.request.id, self.request._meta.verbose_name.capitalize(), self.request.city, self.request.name,
        )


class MealDelivery(BaseDelivery):
    class Meta:
        verbose_name_plural = 'meal deliveries'

    request = models.OneToOneField(
        MealRequest,
        on_delete=models.CASCADE,
        related_name='delivery',
    )
    chef = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        related_name="cooked_meal_deliveries",
        null=True,
        blank=True,
    )
    deliverer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        related_name="delivered_meal_deliveries",
        null=True,
        blank=True,
    )

    def clean(self, *args, **kwargs):
        super(MealDelivery, self).clean(*args, **kwargs)
        if self.dropoff_start and self.dropoff_end and self.date:
            start = datetime.combine(self.date, self.dropoff_start)
            end = datetime.combine(self.date, self.dropoff_end)
            if (start + timedelta(hours=2)) < end and self.status is not Status.DELIVERED:
                raise ValidationError("The delivery window must be two hours or less.")
        if self.deliverer and (not self.dropoff_start or not self.dropoff_end):
            raise ValidationError("Please specify a dropoff window.")

    def send_recipient_meal_notification(self):
        """Send the first notification to a recipient, lets them know that a chef has signed up to cook for them"""
        if not self.request.can_receive_texts:
            raise SendNotificationException("Recipient cannot receive text messages at their phone number")

        # Date is in the format "Weekday Month Year" eg. Sunday November 29
        message = dedent(f"""
            Hi {self.request.name},
            This is a message from The People's Pantry.
            A chef has been arranged to prepare a meal for you for {self.date:%A %B %d}
            Since we depend on volunteers for our deliveries, sometimes we are not able to do all deliveries scheduled for the day. If that’s the case with your delivery, we will inform you by 6 PM on the day of the delivery and your delivery will be rescheduled for the following day.
            Please confirm you got this message and let us know if you can accept the delivery.
            Thank you!
        """)
        send_text(self.request.phone_number, message)
        self.comments.create(comment=f"Sent a text to recipient: {message}")
        logger.info("Sent recipient meal notification text for Meal Request %d to %s", self.request.id, self.request.phone_number)

    def send_recipient_reminder_notification(self):
        """Send a reminder notification to a recipient of the delivery, intended for use on the day of"""
        # Perform validation first that we _can_ send this notification
        if not self.request.can_receive_texts:
            raise SendNotificationException("Recipient cannot receive text messages at their phone number")

        if not (self.dropoff_start and self.dropoff_end):
            raise SendNotificationException("Delivery does not have a dropoff time range scheduled")

        if self.deliverer is None:
            raise SendNotificationException("Delivery does not have a deliverer assigned")

        # Time is in the format "Hour:Minute AM/PM" eg. 09:30 PM
        message = dedent(f"""
            Hi {self.request.name},
            This is a reminder about your delivery from The People’s Pantry today. {self.deliverer.volunteer.name or 'A delivery volunteer'} will be at your home between {self.dropoff_start:%I:%M %p} and {self.dropoff_end:%I:%M %p}.
            Thanks, and stay safe!
        """)
        send_text(self.request.phone_number, message)
        self.comments.create(comment=f"Sent a text to recipient: {message}")
        logger.info("Sent recipient reminder notification text for Meal Request %d to %s", self.request.id, self.request.phone_number)

    def send_recipient_delivery_notification(self):
        """Send a follow-up notification to a recipient, lets them know that a delivery driver will drop if off within a certain time window"""
        # Perform validation first that we _can_ send this notification
        if not self.request.can_receive_texts:
            raise SendNotificationException("Recipient cannot receive text messages at their phone number")

        if not (self.dropoff_start and self.dropoff_end):
            raise SendNotificationException("Delivery does not have a dropoff time range scheduled")

        # Date is in the format "Weekday Month Year" eg. Sunday November 29
        # Time is in the format "Hour:Minute AM/PM" eg. 09:30 PM
        message = dedent(f"""
            Hi {self.request.name},
            This is a message from The People's Pantry.
            Your delivery is scheduled for {self.date:%A %B %d} between {self.dropoff_start:%I:%M %p} and {self.dropoff_end:%I:%M %p}.
            Since we depend on volunteers for our deliveries, sometimes we are not able to do all deliveries scheduled for the day. If that’s the case with your delivery, we will inform you by 6 PM on the day of the delivery and your delivery will be rescheduled for the following day.
            Please confirm you got this message and let us know if you can take the delivery.
            Thank you!
        """)
        send_text(self.request.phone_number, message)
        self.comments.create(comment=f"Sent a text to recipient: {message}")
        logger.info("Sent recipient delivery notification text for Meal Request %d to %s", self.request.id, self.request.phone_number)

    def send_recipient_feedback_request(self):
        """Send a link to our feedback form to a recipient"""
        # Perform validation first that we _can_ send this notification
        if not self.request.can_receive_texts:
            raise SendNotificationException("Recipient cannot receive text messages at their phone number")

        message = dedent(f"""
            Hi {self.request.name},
            This is a message from The People's Pantry.
            If you have any feedback about your recent delivery, we would love to hear it at https://forms.gle/koGhJF1YMee5h3149
            Thank you!
        """)
        send_text(self.request.phone_number, message)
        self.comments.create(comment=f"Sent a text to recipient: {message}")
        logger.info("Sent recipient feedback request text for Meal Request %d to %s", self.request.id, self.request.phone_number)

    def send_chef_reminder_notification(self):
        """Send a reminder notification to the chef"""
        if not self.chef:
            raise SendNotificationException("No chef assigned to this delivery")

        message = dedent(f"""
            Hi {self.chef.volunteer.name},
            This is a message from The People's Pantry.
            Just reminding you of the upcoming meal you're preparing for {self.date:%A %B %d}.
            Please confirm you got this message and let us know if you need any assistance.
            Thank you!
        """)
        send_text(self.chef.volunteer.phone_number, message)
        self.comments.create(comment=f"Sent a text to the chef: {message}")
        logger.info("Sent chef reminder notification text for Meal Request %d to %s", self.request.id, self.chef.volunteer.phone_number)

    def send_deliverer_reminder_notification(self):
        """Send a reminder notification to the deliverer"""
        if not self.deliverer:
            raise SendNotificationException("No deliverer assigned to this delivery")

        message = dedent(f"""
            Hi {self.deliverer.volunteer.name},
            This is a message from The People's Pantry.
            Just reminding you of the upcoming meal you're delivering for {self.date:%A %B %d}.
            Please confirm you got this message and let us know if you need any assistance.
            Thank you!
        """)
        send_text(self.deliverer.volunteer.phone_number, message)
        self.comments.create(comment=f"Sent a text to the deliverer: {message}")
        logger.info("Sent deliverer reminder notification text for Meal Request %d to %s", self.request.id, self.deliverer.volunteer.phone_number)

    def send_detailed_deliverer_notification(self):
        """Send a detailed notification to the deliverer with content for the delivery"""
        if not self.deliverer:
            raise SendNotificationException("No deliverer assigned to this delivery")

        if not self.chef:
            raise SendNotificationException("No chef assigned to this delivery")

        if not self.date:
            raise SendNotificationException("Delivery does not have a date scheduled")

        if not (self.pickup_start and self.pickup_end):
            raise SendNotificationException("Delivery does not have a pickup time range scheduled")

        if not (self.dropoff_start and self.dropoff_end):
            raise SendNotificationException("Delivery does not have a dropoff time range scheduled")

        # Date is in the format "Weekday Month Year" eg. Sunday November 29
        # Time is in the format "Hour:Minute AM/PM" eg. 09:30 PM
        message = dedent(f"""
            Hi {self.deliverer.volunteer.name},
            This is a reminder about your delivery for The People’s Pantry today.
            Pick up the meals from {self.chef.volunteer.name} at {self.chef.volunteer.address}, phone number {self.chef.volunteer.phone_number}, between {self.pickup_start:%I:%M %p} and {self.pickup_end:%I:%M %p}.

            The recipient, {self.request.name} ({self.request.id}) is at {self.request.address}. Notify them when you arrive at {self.request.phone_number}.
            The delivery instructions are: {self.request.delivery_details}.

            Send a text if you have any problems with your delivery, and please let us know when the delivery is completed.
            Thank you for your help!
        """)
        send_text(self.deliverer.volunteer.phone_number, message)
        self.comments.create(comment=f"Sent a text to the deliverer: {message}")
        logger.info("Sent deliverer detailed notification text for Meal Request %d to %s", self.request.id, self.deliverer.volunteer.phone_number)


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


class GroceryRequestComment(CommentModel):
    subject = models.ForeignKey(GroceryRequest, related_name="comments", on_delete=models.CASCADE)


class MealDeliveryComment(CommentModel):
    subject = models.ForeignKey(MealDelivery, related_name="comments", on_delete=models.CASCADE)


class GroceryDeliveryComment(CommentModel):
    subject = models.ForeignKey(GroceryDelivery, related_name="comments", on_delete=models.CASCADE)
