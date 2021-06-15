from datetime import time
import factory
import factory.fuzzy
from django.contrib.auth.models import User

from .models import GroceryRequest, MealRequest
from core.models import Cities
from volunteers.models import Volunteer


class VolunteerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Volunteer

    name = factory.Faker("name")
    phone_number = factory.Faker("phone_number")


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Faker("email")
    username = factory.SelfAttribute("email")
    volunteer = factory.SubFactory(VolunteerFactory)


class GroceryRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GroceryRequest

    name = factory.Faker("name")
    email = factory.Faker("email")
    phone_number = factory.Faker("phone_number")
    address_1 = factory.Faker("street_address")
    address_2 = factory.Faker("building_number")
    city = factory.Faker("random_element", elements=Cities)
    postal_code = factory.Faker("postcode")
    can_receive_texts = factory.Faker("boolean")
    bipoc = factory.Faker("boolean")
    lgbtq = factory.Faker("boolean")
    has_disability = factory.Faker("boolean")
    immigrant_or_refugee = factory.Faker("boolean")
    housing_issues = factory.Faker("boolean")
    sex_worker = factory.Faker("boolean")
    single_parent = factory.Faker("boolean")
    senior = factory.Faker("boolean")
    num_adults = factory.Faker("random_digit_not_null")
    num_children = factory.Faker("random_digit")
    on_behalf_of = factory.Faker("boolean")
    recipient_notified = factory.Faker("boolean")
    accept_terms = True
    covid = factory.Faker("boolean")
    delivery_date = factory.Faker("date_this_month")
    delivery_details = factory.Faker("sentence")


class MealRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MealRequest

    name = factory.Faker("name")
    email = factory.Faker("email")
    phone_number = factory.Faker("phone_number")
    address_1 = factory.Faker("street_address")
    address_2 = factory.Faker("building_number")
    city = factory.Faker("random_element", elements=Cities)
    postal_code = factory.Faker("postcode")
    can_receive_texts = factory.Faker("boolean")
    bipoc = factory.Faker("boolean")
    lgbtq = factory.Faker("boolean")
    has_disability = factory.Faker("boolean")
    immigrant_or_refugee = factory.Faker("boolean")
    housing_issues = factory.Faker("boolean")
    sex_worker = factory.Faker("boolean")
    single_parent = factory.Faker("boolean")
    senior = factory.Faker("boolean")
    num_adults = factory.Faker("random_digit_not_null")
    num_children = factory.Faker("random_digit")
    dairy_free = factory.Faker("boolean")
    gluten_free = factory.Faker("boolean")
    halal = factory.Faker("boolean")
    kosher = factory.Faker("boolean")
    low_carb = factory.Faker("boolean")
    vegan = factory.Faker("boolean")
    vegetarian = factory.Faker("boolean")
    on_behalf_of = factory.Faker("boolean")
    recipient_notified = factory.Faker("boolean")
    accept_terms = True
    covid = factory.Faker("boolean")
    availability = factory.Faker("sentence")
    delivery_details = factory.Faker("sentence")
    delivery_date = factory.Faker("date_this_month")
    pickup_start = time.fromisoformat('12:00')
    pickup_end = time.fromisoformat('13:00')
    dropoff_start = time.fromisoformat('14:00')
    dropoff_end = time.fromisoformat('15:00')
    deliverer = factory.SubFactory(UserFactory)
    chef = factory.SubFactory(UserFactory)
