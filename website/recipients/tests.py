from contextlib import contextmanager
from datetime import date, time
from django.test import TestCase
from textwrap import dedent
from unittest.mock import patch

from django.contrib.auth.models import User

from recipients.models import MealRequest, MealDelivery


class MealDeliveryTextTests(TestCase):
    def setUp(self):
        self.deliverer = User.objects.create(
            username="deliverer@example.com",
            email="deliverer@example.com",
        )
        self.deliverer.volunteer.phone_number = "5555550000"
        self.deliverer.volunteer.name = "Ophelia"
        self.deliverer.volunteer.save()
        self.chef = User.objects.create(
            username="chef@example.com",
            email="chef@example.com",
        )
        self.chef.volunteer.phone_number = "5555551111"
        self.chef.volunteer.name = "Philip"
        self.chef.volunteer.save()
        self.request = MealRequest.objects.create(
            name="Ryan",
            phone_number="5555555555",
            address_1="123 Fake St",
            address_2="Unit 1",
            city="Toronto",
            postal_code="H0H 0H0",
            can_receive_texts=True,
            bipoc=False,
            lgbtq=False,
            has_disability=False,
            immigrant_or_refugee=False,
            housing_issues=False,
            sex_worker=False,
            single_parent=False,
            senior=False,
            num_adults=1,
            num_children=0,
            dairy_free=False,
            gluten_free=False,
            halal=False,
            kosher=False,
            low_carb=False,
            vegan=False,
            vegetarian=False,
            on_behalf_of=False,
            recipient_notified=False,
            accept_terms=True,
            covid=False,
            delivery_details="Deliver to side door",
        )
        self.delivery = MealDelivery.objects.create(
            request=self.request,
            date=date.fromisoformat('2021-03-15'),
            pickup_start=time.fromisoformat('12:00'),
            pickup_end=time.fromisoformat('13:00'),
            dropoff_start=time.fromisoformat('14:00'),
            dropoff_end=time.fromisoformat('15:00'),
            deliverer=self.deliverer,
            chef=self.chef,
        )

    @contextmanager
    def assert_text_matches(self, expected):
        with patch('recipients.models.send_text') as send_text:
            yield

        send_text.assert_called()
        phone_number, message = send_text.mock_calls[0].args
        self.assertEquals(message, expected)

    def test_send_recipient_meal_notification(self):
        expected = dedent("""
            Hi Ryan,
            This is a message from The People's Pantry.
            A chef has been arranged to prepare a meal for you for Monday March 15 for request ID 1.
            Since we depend on volunteers for our deliveries, sometimes we are not able to do all deliveries scheduled for the day. If that’s the case with your delivery, we will inform you by 6 PM on the day of the delivery and your delivery will be rescheduled for the following day.
            Please confirm you got this message and let us know if you can accept the delivery.
            Thank you!
        """)
        with self.assert_text_matches(expected):
            self.delivery.send_recipient_meal_notification()

    def test_send_recipient_reminder_notification(self):
        expected = dedent("""
            Hi Ryan,
            This is a reminder about your delivery from The People’s Pantry today for request ID 1. Ophelia will be at your home between 02:00 PM and 03:00 PM.
            Thanks, and stay safe!
        """)
        with self.assert_text_matches(expected):
            self.delivery.send_recipient_reminder_notification()

    def test_send_recipient_delivery_notification(self):
        expected = dedent("""
            Hi Ryan,
            This is a message from The People's Pantry.
            Your delivery for request ID 1 is scheduled for Monday March 15 between 02:00 PM and 03:00 PM.
            Since we depend on volunteers for our deliveries, sometimes we are not able to do all deliveries scheduled for the day. If that’s the case with your delivery, we will inform you by 6 PM on the day of the delivery and your delivery will be rescheduled for the following day.
            Please confirm you got this message and let us know if you can take the delivery.
            Thank you!
        """)
        with self.assert_text_matches(expected):
            self.delivery.send_recipient_delivery_notification()

    def test_send_recipient_feedback_request(self):
        expected = dedent("""
            Hello Ryan How did you like your meals this week? We appreciate any feedback you have. If you are comfortable with us sharing your anonymized feedback on social media, please let us know - it helps us raise money for the program. If not, that’s okay too.
        """)
        with self.assert_text_matches(expected):
            self.delivery.send_recipient_feedback_request()

    def test_send_chef_reminder_notification(self):
        expected = dedent("""
            Hi Philip,
            Your cooked meals for request ID 1 will be picked up by Ophelia on Monday March 15 between 12:00 PM and 01:00 PM.
            You can contact them at 5555550000.
            If you have more than one delivery, please make sure you are giving the food to the right volunteer.
            Let us know if you have any issues. Thanks!
        """)
        with self.assert_text_matches(expected):
            self.delivery.send_chef_reminder_notification()

    def test_send_deliverer_reminder_notification(self):
        expected = dedent("""
            Hi Ophelia,
            This is a message from The People's Pantry.
            Just reminding you of the upcoming meal you're delivering for Monday March 15.
            Please confirm you got this message and let us know if you need any assistance.
            Thank you!
        """)
        with self.assert_text_matches(expected):
            self.delivery.send_deliverer_reminder_notification()

    def test_send_detailed_deliverer_notification(self):
        expected = dedent("""
            Hi Ophelia,
            This is a reminder about your delivery for The People’s Pantry today.
            Pick up the meals from Philip at   Toronto Ontario , phone number 5555551111, between 12:00 PM and 01:00 PM.

            The recipient, Ryan (1) is at 123 Fake St Unit 1 Toronto Ontario H0H 0H0. Notify them when you arrive at 5555555555.
            The delivery instructions are: Deliver to side door.

            Send a text if you have any problems with your delivery, and please let us know when the delivery is completed.
            Thank you for your help!
        """)
        with self.assert_text_matches(expected):
            self.delivery.send_detailed_deliverer_notification()
