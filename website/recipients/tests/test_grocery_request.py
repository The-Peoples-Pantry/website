from datetime import datetime
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from recipients.models import GroceryRequest


class GroceryRequestTests(TestCase):
    def test_signups_open_friday_at_9am_until_sunday_at_2pm(self):
        # Monday
        with freeze_time(timezone.make_aware(datetime(2021, 7, 5))):
            self.assertTrue(GroceryRequest.requests_paused())

        # Tuesday
        with freeze_time(timezone.make_aware(datetime(2021, 7, 6))):
            self.assertTrue(GroceryRequest.requests_paused())

        # Wednesday
        with freeze_time(timezone.make_aware(datetime(2021, 7, 7))):
            self.assertTrue(GroceryRequest.requests_paused())

        # Thursday
        with freeze_time(timezone.make_aware(datetime(2021, 7, 8))):
            self.assertTrue(GroceryRequest.requests_paused())

        # Friday (Early morning)
        with freeze_time(timezone.make_aware(datetime(2021, 7, 9))):
            self.assertTrue(GroceryRequest.requests_paused())

        # Friday (at 9am)
        with freeze_time(timezone.make_aware(datetime(2021, 7, 9, hour=9))):
            self.assertFalse(GroceryRequest.requests_paused())

        # Saturday
        with freeze_time(timezone.make_aware(datetime(2021, 7, 10))):
            self.assertFalse(GroceryRequest.requests_paused())

        # Sunday (Morning)
        with freeze_time(timezone.make_aware(datetime(2021, 7, 11, hour=8))):
            self.assertFalse(GroceryRequest.requests_paused())

        # Sunday (at 2pm)
        with freeze_time(timezone.make_aware(datetime(2021, 7, 11, hour=14))):
            self.assertTrue(GroceryRequest.requests_paused())
