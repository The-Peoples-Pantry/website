from django.db import models

DEFAULT_LENGTH = 256
NAME_LENGTH = DEFAULT_LENGTH
PHONE_NUMBER_LENGTH = 20
ADDRESS_LENGTH = DEFAULT_LENGTH
CITY_LENGTH = 50
POSTAL_CODE_LENGTH = 7  # Optional space
DAY_LENGTH = 9  # Longest is "Wednesday"


class Cities(models.TextChoices):
    AJAX = 'Ajax', 'Ajax'
    AURORA = 'Aurora', 'Aurora'
    BRAMPTON = 'Brampton', 'Brampton'
    BROCK = 'Brock', 'Brock'
    BURLINGTON = 'Burlington', 'Burlington'
    CALEDON = 'Caledon', 'Caledon'
    CLARINGTON = 'Clarington', 'Clarington'
    EAST_GWILIMBURY = 'East Gwilimbury', 'East Gwilimbury'
    EAST_YORK = 'East York', 'East York'
    ETOBICOKE = 'Etobicoke', 'Etobicoke'
    GEORGINA = 'Georgina', 'Georgina'
    HALTON_HILLS = 'Halton Hills', 'Halton Hills'
    HAMILTON = 'Hamilton', 'Hamilton'
    KING = 'King', 'King'
    MAPLE = 'Maple', 'Maple'
    MARKHAM = 'Markham', 'Markham'
    MILTON = 'Milton', 'Milton'
    MISSISSAUGA = 'Mississauga', 'Mississauga'
    NEWMARKET = 'Newmarket', 'Newmarket'
    NORTH_YORK = 'North York', 'North York'
    OAKVILLE = 'Oakville', 'Oakville'
    OSHAWA = 'Oshawa', 'Oshawa'
    PICKERING = 'Pickering', 'Pickering'
    RICHMOND_HILL = 'Richmond Hill', 'Richmond Hill'
    SCARBOROUGH = 'Scarborough', 'Scarborough'
    SCUGOG = 'Scugog', 'Scugog'
    STOUFFVILLE = 'Stouffville', 'Stouffville'
    THORNHILL = 'Thornhill', 'Thornhill'
    TORONTO = 'Toronto', 'Toronto (downtown, east/west ends)'
    UXBRIDGE = 'Uxbridge', 'Uxbridge'
    VAUGHAN = 'Vaughan', 'Vaughan'
    WHITBY = 'Whitby', 'Whitby'
    YORK = 'York', 'York'


class Days(models.TextChoices):
    MONDAY = 'MONDAY'
    TUESDAY = 'TUESDAY'
    WEDNESDAY = 'WEDNESDAY'
    THURSDAY = 'THURSDAY'
    FRIDAY = 'FRIDAY'
    SATURDAY = 'SATURDAY'
    SUNDAY = 'SUNDAY'


class TimePeriods(models.TextChoices):
    PERIOD_12_14 = '12 - 2 PM'
    PERIOD_14_16 = '2 - 4 PM'
    PERIOD_16_18 = '4 - 6 PM'
    PERIOD_16_20 = '6 - 8 PM'
    PERIOD_20_22 = '8 - 10 PM'


class MealRequest(models.Model):
    # Information about the recipient
    name = models.CharField(max_length=NAME_LENGTH)
    email = models.EmailField()
    phone_number = models.CharField(max_length=PHONE_NUMBER_LENGTH)
    can_receive_texts = models.BooleanField()
    address_1 = models.CharField(max_length=ADDRESS_LENGTH)
    address_2 = models.CharField(max_length=ADDRESS_LENGTH)
    city = models.CharField(
        max_length=CITY_LENGTH,
        choices=Cities.choices,
        default=Cities.TORONTO,
    )
    postal_code = models.CharField(max_length=POSTAL_CODE_LENGTH)
    notes = models.TextField(blank=True)

    # Information about community status
    bipoc = models.BooleanField()
    lgbtq = models.BooleanField()
    has_disability = models.BooleanField()
    immigrant_or_refugee = models.BooleanField()
    housing_issues = models.BooleanField()
    sex_worker = models.BooleanField()
    single_parent = models.BooleanField()

    # Information about the request itself
    num_adults = models.PositiveSmallIntegerField()
    num_children = models.PositiveSmallIntegerField()
    children_ages = models.CharField(max_length=DEFAULT_LENGTH)
    food_allergies = models.TextField()
    food_preferences = models.TextField()
    will_accept_vegan = models.BooleanField(default=True)
    will_accept_vegetarian = models.BooleanField(default=True)

    # Information about the delivery
    can_meet_for_delivery = models.BooleanField()
    delivery_details = models.TextField()
    available_days = models.CharField(max_length=DEFAULT_LENGTH)
    available_time_periods = models.CharField(max_length=DEFAULT_LENGTH)

    # Dietary restrictions
    dairy_free = models.BooleanField()
    gluten_free = models.BooleanField()
    halal = models.BooleanField()
    low_carb = models.BooleanField()
    vegan = models.BooleanField()
    vegetarian = models.BooleanField()

    # Information about the requester
    # Will be null if on_behalf_of is False, indicating request was by the recipient
    on_behalf_of = models.BooleanField()
    recipient_notified = models.BooleanField()
    requester_name = models.CharField(max_length=NAME_LENGTH, null=True)
    requester_email = models.EmailField(null=True)
    requester_phone_number = models.CharField(max_length=PHONE_NUMBER_LENGTH)

    # Legal
    accept_terms = models.BooleanField()

    # System
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
