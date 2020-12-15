import csv
import logging
from textwrap import dedent
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import get_connection
from django.contrib.auth.models import User
from django.db.utils import IntegrityError

from volunteers.models import VolunteerRoles, VolunteerApplication
from website.mail import custom_send_mail

logging.basicConfig(level=logging.INFO)

# Fields
NAME_FIELD = 'Full name:'
EMAIL_FIELD = 'Email address:'
PHONE_FIELD = 'Phone number:'
# NOTE: Full address is included in address_1; parsing would probably require geocoding query.
#       Likely better to stick with defaults in `address_2` and `postal_code` for now.
ADDRESS_FIELD = 'Full address (including any applicable apartment/unit/suite number):'
ROLES_FIELD = 'Would you like to...? Check all that apply.'
PRONOUNS_FIELD = 'Preferred pronouns:'
COOKING_PREFS_FIELD = 'What do you prefer to cook/bake? Check all that apply.'
FOOD_TYPES_FIELD = 'What kind of meals/baked goods are you able to prepare? Check all that apply. '
CLEANING_SUPPLIES_FIELD = 'Do you have cleaning supplies (soap, disinfectant, etc.) to clean your hands and kitchen?'
PPE_FIELD = 'Do you have a mask you can use while cooking/baking and packaging food?'
CHEF_DAYS_AVAILABLE_FIELD = 'What days of the week are you able to cook/bake? '
CHEF_TOTAL_HOURS_FIELD = 'How many hours can you spend cooking/baking per week?'
DELIVERY_DAYS_AVAILABLE_FIELD = 'What days of the week are you able to deliver? Check all that apply.'
BAKING_VOLUME_FIELD = 'For BAKERS: how many "units" of baked goods can you bake each time? '
TRANSPORTATION_FIELD = 'What means of transportation would you be using for deliveries? Check all that apply.'
REQUIRED_FIELDS = [NAME_FIELD, EMAIL_FIELD, ADDRESS_FIELD, PHONE_FIELD]

# Roles
CHEF_INDICATOR = 'cook/bake'
DELIVERER_INDICATOR = 'deliver'
ADMINISTRATOR_INDICATOR = 'administrative'


class ValidationError(Exception):
    def __init__(self, message):
        self.message = message


class Command(BaseCommand):
    help = 'Migrate volunteers from PPT "Volunteers Directory" Google Sheet.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            help='Path to CSV export of Google Sheet with volunteer information.',
            required=True
        )

    def handle(self, *args, **kwargs):
        # dash replace with underscore
        csv_path = kwargs['csv']

        with open(csv_path) as csv_input:
            entries = list(csv.DictReader(csv_input))

        # Create a mail connection to avoid opening a new one for each email
        with get_connection() as connection:
            self.connection = connection
            for index, entry in enumerate(entries):
                line_number = index + 1
                try:
                    self.create_user(entry)
                except IntegrityError:
                    self.stdout.write(f'Skipping line {line_number}: already exists')
                except ValidationError as e:
                    self.stdout.write(self.style.NOTICE(
                        f'Skipping line {line_number}: {e.message}'
                    ))

    def get_roles(self, entry: dict):
        field = entry[ROLES_FIELD].lower()
        roles = []
        if CHEF_INDICATOR in field:
            roles.append(VolunteerRoles.CHEFS)
        if DELIVERER_INDICATOR in field:
            roles.append(VolunteerRoles.DELIVERERS)
        if ADMINISTRATOR_INDICATOR in field:
            self.stdout.write('Skipping administrative role')
        return roles

    def send_invite_email(self, email, name):
        custom_send_mail(
            "Welcome to The People's Pantry's new website",
            dedent(f"""
                Hi {name},

                You are receiving this email because of your prior work as a volunteer with The People's Pantry Toronto.

                Earlier this year, we paused our meal delivery program to improve our processes and set up a more sustainable working process.

                Today, we are pleased to welcome you back and invite you to visit our new website, through which we will be coordinating the project: https://www.thepeoplespantryto.com

                The website will be the new place where our recipients can submit requests and where you can log in to offer your help as a driver or as a chef. You will be able to filter requests by location, size, and dietary restrictions. You will also be able to see a dashboard of all of the requests that you're currently signed up for. Please keep an eye on the dashboard to keep on top of the requests you have signed up to fulfill.

                We have imported your information from our previous system. To finalize your registration for the new website, please create a password by going to https://www.thepeoplespantryto.com/accounts/password_reset/ and entering your email address. We will then email you a link that will allow you to set your password.

                If you are interested in returning as a volunteer, please review the Volunteer Guidelines to refresh your memory: https://bit.ly/3njYU1J

                Finally, please review The People’s Pantry Code of Conduct here: https://bit.ly/3oQ24dN which lays out our organizing principles, and defines boundaries for working with other volunteers and our community. Our volunteers are the face of The People’s Pantry; we want to ensure a respectful and sustainable environment for all of us.

                We look forward to continuing our work with you!

                With thanks,
                The People's Pantry
            """),
            [email],
            reply_to=settings.VOLUNTEER_COORDINATORS_EMAIL,
            connection=self.connection,
        )

    def validate(self, entry: dict):
        for field in REQUIRED_FIELDS:
            if not entry.get(field):
                raise ValidationError(f'Missing required field ({field})')

    def create_user(self, entry: dict):
        self.validate(entry)

        name = entry[NAME_FIELD]
        email = entry[EMAIL_FIELD]

        # NOTE: receiver enforces that volunteer object is created here as well
        user = User.objects.create(username=email, email=email)
        random_password = User.objects.make_random_password()
        user.set_password(random_password)
        user.save()

        # Volunteer fields
        user.volunteer.name = name
        user.volunteer.email = email
        user.volunteer.address_1 = entry[ADDRESS_FIELD]
        user.volunteer.phone_number = entry[PHONE_FIELD]
        user.volunteer.pronouns = entry[PRONOUNS_FIELD]
        user.volunteer.cooking_prefs = entry[COOKING_PREFS_FIELD]
        user.volunteer.food_types = entry[FOOD_TYPES_FIELD]
        user.volunteer.days_available = entry[CHEF_DAYS_AVAILABLE_FIELD] or entry[DELIVERY_DAYS_AVAILABLE_FIELD]
        user.volunteer.total_hours_available = entry[CHEF_TOTAL_HOURS_FIELD]
        user.volunteer.baking_volume = entry[BAKING_VOLUME_FIELD]
        user.volunteer.transportation_options = entry[TRANSPORTATION_FIELD]
        if entry[CLEANING_SUPPLIES_FIELD] == 'Yes':
            user.volunteer.have_cleaning_supplies = True
        if entry[PPE_FIELD] == 'Yes':
            user.volunteer.have_ppe = True
        user.volunteer.save()

        for role in self.get_roles(entry):
            application = VolunteerApplication.objects.create(user=user, role=role)
            application.approve()

        self.send_invite_email(email, name)

        self.stdout.write(self.style.SUCCESS(f'Successfully added user {email}'))
