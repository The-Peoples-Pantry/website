import csv
import logging
import operator
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.utils import IntegrityError

from volunteers.models import VolunteerRoles, VolunteerApplication

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
            reader = list(csv.DictReader(csv_input))

        for index, entry in enumerate(reader):
            line_number = index + 1
            try:
                self.create_user(entry)
            except IntegrityError:
                self.stdout.write(f'Skipping line {line_number}: already exists')
            except ValidationError as e:
                self.stdout.write(self.style.NOTICE(
                    f'Skipping line {line_number}: {e.message}'
                ))

    def format_entry(self, entry: dict):
        return ', '.join(operator.attrgetter(REQUIRED_FIELDS)())

    def split_name(self, name: str):
        first, *rest = name.split(' ')
        return first, ' '.join(rest)

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

    def validate(self, entry: dict):
        for field in REQUIRED_FIELDS:
            if not entry.get(field):
                raise ValidationError(f'Missing required field ({field})')

    def create_user(self, entry: dict):
        self.validate(entry)

        full_name = entry[NAME_FIELD]
        email = entry[EMAIL_FIELD]
        address = entry[ADDRESS_FIELD]
        phone_number = entry[PHONE_FIELD]
        pronouns = entry[PRONOUNS_FIELD]
        cooking_prefs = entry[COOKING_PREFS_FIELD]
        food_types = entry[FOOD_TYPES_FIELD]
        cleaning_supplies = entry[CLEANING_SUPPLIES_FIELD]
        ppe = entry[PPE_FIELD]
        first_name, last_name = self.split_name(full_name)

        # NOTE: receiver enforces that volunteer object is created here as well
        user = User.objects.create(
            username=email,
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        random_password = User.objects.make_random_password()
        user.set_password(random_password)
        user.save()

        # Volunteer fields
        user.volunteer.name = full_name
        user.volunteer.email = email
        user.volunteer.address_1 = address
        user.volunteer.phone_number = phone_number
        user.volunteer.pronouns = pronouns
        user.volunteer.cooking_prefs = cooking_prefs
        user.volunteer.food_types = food_types
        if cleaning_supplies == 'Yes':
            user.volunteer.have_cleaning_supplies = True
        if ppe == 'Yes':
            user.volunteer.have_ppe = True
        user.volunteer.save()

        for role in self.get_roles(entry):
            application = VolunteerApplication.objects.create(user=user, role=role)
            application.approve()

        self.stdout.write(self.style.SUCCESS(f'Successfully added user {user.id}'))
