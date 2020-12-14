from textwrap import dedent
from django.db import models
from django.contrib.auth.models import Group, User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from core.models import ContactInfo
from website.mail import custom_send_mail


class CookingTypes(models.TextChoices):
    COOKING = 'Cooking', 'Cooking'
    BAKING = 'Baking', 'Baking'


class FoodTypes(models.TextChoices):
    MEAT = 'Meat', 'Meat'
    VEGAN = 'Vegan', 'Vegan'
    VEGETARIAN = 'Vegetarian', 'Vegetarian'
    DAIRY_FREE = 'Dairy-free', 'Dairy-free'
    GLUTEN_FREE = 'Gluten-free', 'Gluten-free'
    LOW_CARB = 'Low carb', 'Low carb'
    HALAL = 'Halal', 'Halal'
    KOSHER = 'Kosher', 'Kosher'


class TransportationTypes(models.TextChoices):
    SUV = 'SUV or Truck', 'SUV or Truck'
    MED_CAR = 'Medium-sized car', 'Medium-sized car'
    SM_CAR = 'Small car', 'Small car'
    BIKE_SUMMER = 'Bike - Spring to Fall deliveries only', 'Bike - Spring to Fall deliveries only'
    BIKE_ALL = 'Bike - Can deliver in snow', 'Bike - Can deliver in snow'


class DaysOfWeek(models.TextChoices):
    MONDAY = 'Monday'
    TUESDAY = 'Tuesday'
    WEDNESDAY = 'Wednesday'
    THURSDAY = 'Thursday'
    FRIDAY = 'Friday'
    SATURDAY = 'Saturday'
    SUNDAY = 'Sunday'


# These choice values must match up with the name of the Groups
class VolunteerRoles(models.TextChoices):
    CHEFS = 'Chefs'
    DELIVERERS = 'Deliverers'
    ORGANIZERS = 'Organizers'


class Volunteer(ContactInfo):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="volunteer"
    )
    pronouns = models.CharField(
        "Pronouns",
        help_text="Please include all of your pronouns",
        max_length=settings.DEFAULT_LENGTH,
        null=True,
        blank=True
    )
    days_available = models.CharField(
        "Days available",
        help_text="What days of the week are you available to volunteer?",
        max_length=settings.DEFAULT_LENGTH,
        null=True
    )
    total_hours_available = models.CharField(
        "Total commitment",
        help_text="How many hours a week are your willing to volunteer?",
        max_length=settings.DEFAULT_LENGTH,
        null=True
    )
    recurring_time_available = models.CharField(
        "Recurring availability",
        help_text="Are there any times when you're consistently available? E.g. Mondays from 1-6pm, etc.",
        max_length=settings.DEFAULT_LENGTH,
        null=True
    )
    have_ppe = models.BooleanField(
        "PPE",
        help_text="Do you have access to personal protective equipment such as masks, gloves, etc?",
        default=False
    )

    # Fields for cooks only
    cooking_prefs = models.CharField(
        "Cooking type",
        help_text="What do you prefer to cook/bake? Check all that apply.",
        max_length=settings.DEFAULT_LENGTH,
        null=True,
        blank=True
    )
    food_types = models.CharField(
        "Food types",
        help_text="What kind of meals/baked goods are you able to prepare? Check all that apply.",
        max_length=settings.DEFAULT_LENGTH,
        null=True,
        blank=True
    )
    have_cleaning_supplies = models.BooleanField(
        "Cleaning supplies",
        help_text="Do you have cleaning supplies (soap, disinfectant, etc.) to clean your hands and kitchen?",
        null=True,
        blank=True
    )
    baking_volume = models.CharField(
        "Baking volume",
        help_text="For BAKERS: how many 'units' of baked goods can you bake each time? E.g. 48 cookies, 24 cinnamon buns, etc",
        max_length=settings.DEFAULT_LENGTH,
        null=True,
        blank=True
    )

    # Fields for delivery people only
    transportation_options = models.CharField(
        "Transportation options",
        help_text="What means of transportation do you have access to for deliveries? Check all that apply.",
        max_length=settings.DEFAULT_LENGTH,
        null=True,
        blank=True
    )
    training_complete = models.BooleanField("Training Complete", default=False)


class VolunteerApplication(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'role'], name='unique role per user application')
        ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='volunteer_applications'
    )
    role = models.CharField(
        max_length=50,
        choices=VolunteerRoles.choices,
    )
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def has_applied(cls, user, role: str):
        return cls.objects.filter(user=user, role=role).exists()

    def approve(self):
        """Approves the application if it hasn't been already.
        Returns False if the application has already been approved, else True
        """
        if self.approved:
            return False
        group = Group.objects.get(name=self.role)
        self.user.groups.add(group)
        self.approved = True
        self.save()
        return True

    def send_confirmation_email(self):
        custom_send_mail(
            "Confirming your The People's Pantry volunteer application",
            dedent(f"""
                Just confirming that we received your request to join the {self.role} volunteer team for The People's Pantry.
                We will be in touch with further training materials
            """),
            [self.user.email]
        )


# When user is created or saved, also save volunteer
@receiver(post_save, sender=User)
def save_volunteer(sender, instance, created, **kwargs):
    if created:
        Volunteer.objects.create(user=instance)
    instance.volunteer.save()
