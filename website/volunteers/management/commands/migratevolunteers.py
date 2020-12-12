import csv
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db.utils import IntegrityError
from volunteers.models import Volunteer
import logging

logging.basicConfig(level=logging.DEBUG)

NAME_FIELD = 'Full name:'
EMAIL_FIELD = 'Email address:'
PHONE_FIELD = 'Phone number:'
ADDRESS_FIELD = 'Full address (including any applicable apartment/unit/suite number):'
ROLES_FIELD = 'Would you like to...? Check all that apply.'
REQUIRED_FIELDS = [NAME_FIELD, EMAIL_FIELD, PHONE_FIELD]


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
            reader = csv.DictReader(csv_input)
            for entry in reader:
                self.csv_to_django(entry)

    def friendly_entry(self, entry: dict):
        return ', '.join(
            map(
                lambda field: entry[field],
                REQUIRED_FIELDS
            )
        )

    def csv_to_django(entry: dict):
        for field in REQUIRED_FIELDS:
            if field not in entry or not entry[field]:
                logging.warning(
                    f'Required entry `{field}` is missing or empty, skipping entry: {str(list(entry.values()))}'
                )
                return

        chefs = Group.objects.get(name='Chefs')
        deliverers = Group.objects.get(name='Deliverers')
        organizers = Group.objects.get(name='Organizers')

        try:
            full_name = entry[NAME_FIELD].split(' ')
            first_name = full_name[0]
            last_name = ' '.join(full_name[1:])
            email = entry[EMAIL_FIELD]
            user = User.objects.create(username=email, first_name=first_name, last_name=last_name, email=email)

            random_password = User.objects.make_random_password()
            user.set_password(random_password)

            # NOTE: receiver enforces that volunteer object is created here as well
            user.save()

            # Volunteer fields
            volunteer = Volunteer.objects.get(user=user)
            volunteer.address_1 = entry[ADDRESS_FIELD]
            # NOTE: Full address is included in address_1; parsing would probably require geocoding query.
            #       Likely better to stick with defaults in `address_2` and `postal_code` for now.
            volunteer.phone_number = entry[PHONE_FIELD]

            # Role
            role_selection = entry[ROLES_FIELD].lower()
            if role_selection:
                if 'cook/bake' in role_selection:
                    chefs.user_set.add(user)
                elif 'deliver' in role_selection:
                    deliverers.user_set.add(user)
                elif 'administrative' in role_selection:
                    organizers.user_set.add(user)
                else:
                    logging.warning(
                        f'Unknown role selection {role_selection} for entry: {self.friendly_entry(entry, required_fields)}'
                    )

            volunteer.save()

        except KeyError as e:
            raise KeyError(f'Entry is missing a required field {str(e)}: {self.friendly_entry(entry, required_fields)}')

        except IntegrityError as e:
            logging.warning(f'SKIPPING ENTRY: {str(e)} for entry: {self.friendly_entry(entry, required_fields)}')