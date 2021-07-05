from datetime import datetime
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from recipients.factories import MealRequestFactory
from recipients.models import MealRequest


class MealRequestTests(TestCase):
    def test_signups_open_sunday_morning_till_noon(self):
        # Monday
        with freeze_time(timezone.make_aware(datetime(2021, 7, 5))):
            self.assertTrue(MealRequest.requests_paused())

        # Tuesday
        with freeze_time(timezone.make_aware(datetime(2021, 7, 6))):
            self.assertTrue(MealRequest.requests_paused())

        # Wednesday
        with freeze_time(timezone.make_aware(datetime(2021, 7, 7))):
            self.assertTrue(MealRequest.requests_paused())

        # Thursday
        with freeze_time(timezone.make_aware(datetime(2021, 7, 8))):
            self.assertTrue(MealRequest.requests_paused())

        # Friday
        with freeze_time(timezone.make_aware(datetime(2021, 7, 9))):
            self.assertTrue(MealRequest.requests_paused())

        # Saturday
        with freeze_time(timezone.make_aware(datetime(2021, 7, 10))):
            self.assertTrue(MealRequest.requests_paused())

        # Sunday (Morning)
        with freeze_time(timezone.make_aware(datetime(2021, 7, 11, 8))):
            self.assertTrue(MealRequest.requests_paused())

        # Sunday (at Noon)
        with freeze_time(timezone.make_aware(datetime(2021, 7, 11, 12))):
            self.assertFalse(MealRequest.requests_paused())