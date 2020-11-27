from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from recipients.models import Cities, AddressModel


def get_group_string(group_set):
    groups = []
    if len(group_set) == 0:
        return ""

    for group in group_set:
        groups.append(group.name)
    return "(" + ", ".join(groups) + ")"


# These choice values must match up with the name of the Groups
class VolunteerRoles(models.TextChoices):
    CHEFS = 'Chefs'
    DELIVERERS = 'Deliverers'
    ORGANIZERS = 'Organizers'


class Volunteer(AddressModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="volunteer"
    )
    address_1 = models.CharField(
        "Address line 1",
        help_text="Street name and number",
        max_length=settings.ADDRESS_LENGTH,
        blank=True
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
    phone_number = models.CharField(
        "Phone number",
        help_text="Use the format 555-555-5555",
        max_length=settings.PHONE_NUMBER_LENGTH,
    )
    postal_code = models.CharField(
        "Postal code",
        max_length=settings.POSTAL_CODE_LENGTH,
        blank=True
    )
    training_complete = models.BooleanField("Training Complete", default=False)

    def __str__(self):
        return "%s %s" % (self.user, get_group_string(self.user.groups.all()))


class VolunteerApplication(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'role'], name='unique role per user application')
        ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    role = models.CharField(
        max_length=50,
        choices=VolunteerRoles.choices,
    )
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# When user is created or saved, also save volunteer
@receiver(post_save, sender=User)
def save_volunteer(sender, instance, created, **kwargs):
    if created:
        Volunteer.objects.create(user=instance)
    instance.volunteer.save()
