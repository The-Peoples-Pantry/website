import faker
import factory
import factory.fuzzy
import factory.django
import random
import datetime
from django.core.management.base import BaseCommand
from recipients.models import MealRequest, Cities

factory.Faker.add_provider(faker.providers.phone_number)
factory.Faker.add_provider(faker.providers.address)
factory.Faker._DEFAULT_LOCALE = 'en_CA'


def fuzzy_choices(choices):
    values = [choice.value for choice in choices]
    k = random.randint(0, len(values))
    results = list(random.sample(values, k))
    return str(results)


def fuzzy_date(start, end):
    return (start + datetime.timedelta(
        seconds=random.randint(0, int((end - start).total_seconds())),
    )).date()


class MealRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MealRequest

    name = factory.Faker('name')
    email = factory.Faker('email')
    phone_number = factory.Faker('phone_number')
    can_receive_texts = factory.Faker('boolean')
    address_1 = factory.Faker('street_address')
    address_2 = factory.Faker('building_number')
    city = factory.fuzzy.FuzzyChoice(Cities)
    postal_code = factory.Faker('postcode')
    notes = factory.Faker('sentence')

    bipoc = factory.Faker('boolean')
    lgbtq = factory.Faker('boolean')
    has_disability = factory.Faker('boolean')
    immigrant_or_refugee = factory.Faker('boolean')
    housing_issues = factory.Faker('boolean')
    sex_worker = factory.Faker('boolean')
    single_parent = factory.Faker('boolean')

    num_adults = factory.Faker('random_digit')
    num_children = factory.Faker('random_digit')
    children_ages = "1, 2, 3"
    food_allergies = factory.Faker('sentence')
    food_preferences = factory.Faker('sentence')

    will_accept_vegan = factory.Faker('boolean')
    will_accept_vegetarian = factory.Faker('boolean')

    can_meet_for_delivery = factory.Faker('boolean')
    delivery_details = factory.Faker('sentence')
    availability = factory.Faker('sentence')

    dairy_free = factory.Faker('boolean')
    gluten_free = factory.Faker('boolean')
    halal = factory.Faker('boolean')
    low_carb = factory.Faker('boolean')
    vegan = factory.Faker('boolean')
    vegetarian = factory.Faker('boolean')

    on_behalf_of = factory.Faker('boolean')
    recipient_notified = factory.Faker('boolean')
    requester_name = factory.Faker('name')
    requester_email = factory.Faker('email')
    requester_phone_number = factory.Faker('phone_number')

    accept_terms = True


class Command(BaseCommand):
    help = 'Seed fake MealRequests into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of MealRequests to generate'
        )

    def handle(self, *args, **options):
        count = options['count']

        for i in range(count):
            obj = MealRequestFactory.create()

            if generate_date:
                start = datetime.datetime.now()
                end = start + datetime.timedelta(days=10)

            obj.save()

            assert obj.id is not None, "Something went wrong"
        self.stdout.write(self.style.SUCCESS(f'Created {count} MealRequest items'))