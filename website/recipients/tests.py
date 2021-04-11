from datetime import date, time
from django.test import TestCase
from textwrap import dedent
from unittest.mock import MagicMock

from django.contrib.auth.models import User

from recipients.models import MealRequest, GroceryRequest


class MealRequestTextTests(TestCase):
    def setUp(self):
        self.api = MagicMock()
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
            delivery_date=date.fromisoformat('2021-03-15'),
            pickup_start=time.fromisoformat('12:00'),
            pickup_end=time.fromisoformat('13:00'),
            dropoff_start=time.fromisoformat('14:00'),
            dropoff_end=time.fromisoformat('15:00'),
            deliverer=self.deliverer,
            chef=self.chef,
        )

    def test_send_recipient_meal_notification(self):
        expected = dedent("""
            Hi Ryan,
            This is a message from The People's Pantry.
            A chef has been arranged to prepare a meal for you for Monday March 15 for request ID 1.
            Since we depend on volunteers for our deliveries, sometimes we are not able to do all deliveries scheduled for the day. If that’s the case with your delivery, we will inform you by 6 PM on the day of the delivery and your delivery will be rescheduled for the following day.
            Please confirm you got this message and let us know if you can accept the delivery.
            Thank you!
        """).strip()
        self.request.send_recipient_meal_notification(self.api)
        self.api.send_text.assert_called_with(self.request.phone_number, expected, "default")

    def test_send_recipient_reminder_notification(self):
        expected = dedent("""
            Hi Ryan,
            This is a reminder about your delivery from The People’s Pantry today for request ID 1. Ophelia will be at your home between 02:00 PM and 03:00 PM.
            Thanks, and stay safe!
        """).strip()
        self.request.send_recipient_reminder_notification(self.api)
        self.api.send_text.assert_called_with(self.request.phone_number, expected, "default")

    def test_send_recipient_delivery_notification(self):
        expected = dedent("""
            Hi Ryan,
            This is a message from The People's Pantry.
            Your delivery for request ID 1 is scheduled for Monday March 15 between 02:00 PM and 03:00 PM.
            Since we depend on volunteers for our deliveries, sometimes we are not able to do all deliveries scheduled for the day. If that’s the case with your delivery, we will inform you by 6 PM on the day of the delivery and your delivery will be rescheduled for the following day.
            Please confirm you got this message and let us know if you can take the delivery.
            Thank you!

            Reply STOP to unsubscribe
        """).strip()
        self.request.send_recipient_delivery_notification(self.api)
        self.api.send_text.assert_called_with(self.request.phone_number, expected, "default")

    def test_send_recipient_feedback_request(self):
        expected = dedent("""
            Hello Ryan How did you like your meals this week? We appreciate any feedback you have. If you are comfortable with us sharing your anonymized feedback on social media, please let us know - it helps us raise money for the program. If not, that’s okay too.
        """).strip()
        self.request.send_recipient_feedback_request(self.api)
        self.api.send_text.assert_called_with(self.request.phone_number, expected, "default")

    def test_send_chef_reminder_notification(self):
        expected = dedent("""
            Hi Philip,
            This is a message from The People's Pantry.
            Your cooked meals for request ID 1 will be picked up by Ophelia on Monday March 15 between 12:00 PM and 01:00 PM.
            You can contact them at 5555550000.
            If you have more than one delivery, please make sure you are giving the food to the right volunteer.
            Let us know if you have any issues. Thanks!

            Reply STOP to unsubscribe
        """).strip()
        self.request.send_chef_reminder_notification(self.api)
        self.api.send_text.assert_called_with(self.chef.volunteer.phone_number, expected, "default")

    def test_send_deliverer_reminder_notification(self):
        expected = dedent("""
            Hi Ophelia,
            This is a message from The People's Pantry.
            Just reminding you of the upcoming meal you're delivering for Monday March 15.
            Please confirm you got this message and let us know if you need any assistance.
            Thank you!

            Reply STOP to unsubscribe
        """).strip()
        self.request.send_deliverer_reminder_notification(self.api)
        self.api.send_text.assert_called_with(self.deliverer.volunteer.phone_number, expected, "default")

    def test_send_detailed_deliverer_notification(self):
        expected = dedent("""
            Hi Ophelia,
            This is a reminder about your delivery for The People’s Pantry today.
            Pick up the meals from Philip at   Toronto Ontario , phone number 5555551111, between 12:00 PM and 01:00 PM.

            The recipient, Ryan (1) is at 123 Fake St Unit 1 Toronto Ontario H0H 0H0. Notify them when you arrive at 5555555555.
            The delivery instructions are: Deliver to side door.

            Send a text if you have any problems with your delivery, and please let us know when the delivery is completed.
            Thank you for your help!
        """).strip()
        self.request.send_detailed_deliverer_notification(self.api)
        self.api.send_text.assert_called_with(self.deliverer.volunteer.phone_number, expected, "default")


class GroceryRequestTextTests(TestCase):
    def setUp(self):
        self.api = MagicMock()
        self.request = GroceryRequest.objects.create(
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
            on_behalf_of=False,
            recipient_notified=False,
            accept_terms=True,
            covid=False,
            delivery_date=date.fromisoformat('2021-03-15'),
            delivery_details="Deliver to side door",
        )

    def test_send_recipient_scheduled_notification(self):
        expected = dedent("""
            Hi Ryan,
            This is a message from The People's Pantry.
            Your delivery has been scheduled for Monday March 15. FoodShare will be delivering your box between 10 AM and 9 PM at your door and/or following your delivery instructions. Please make sure to check your phone regularly so the delivery driver can communicate with you easily.
            Delivery dates may vary to balance daily orders or if the driver did not get to the delivery by 9 PM. If there are any changes, we will do our best to communicate with you ahead of time.
            The gift card will be sent to you on the same day of the delivery.
            Thank you and stay safe!

            Reply STOP to unsubscribe
        """).strip()
        self.request.send_recipient_scheduled_notification(api=self.api)
        self.api.send_text.assert_called_with(self.request.phone_number, expected, "groceries")

    def test_send_recipient_allergy_notification(self):
        expected = dedent("""
            Hi Ryan,
            This is a message from The People's Pantry.
            Because the FoodShare boxes this week included a food which you listed as an allergy, instead of the produce box, you will receive an extra gift card equal to the box’s value.
            Please feel free to be in touch with any questions, comments, or concerns.
        """).strip()
        self.request.send_recipient_allergy_notification(api=self.api)
        self.api.send_text.assert_called_with(self.request.phone_number, expected, "groceries")

    def test_send_recipient_reminder_notification(self):
        expected = dedent("""
            Hello Ryan,
            This is a message from The People's Pantry.
            Your FoodShare produce box is scheduled to be delivered today. Just a reminder that boxes are delivered until 9 PM.  Please let us know once you receive your grocery box.
            If you don’t receive your box by that time today, please let us know by replying to this message. When delivery drivers didn’t get to do the delivery because they ran out of time, they will schedule your delivery for the following day.
            Gift cards are delivered separately, either by mail (for physical gift cards, timing will depend on Canada post) or via email (be sure to check your spam folder!).
            Thanks, and stay safe!
        """).strip()
        self.request.send_recipient_reminder_notification(api=self.api)
        self.api.send_text.assert_called_with(self.request.phone_number, expected, "groceries")

    def test_send_recipient_rescheduled_notification(self):
        expected = dedent("""
            Hello Ryan,
            This is a message from The People's Pantry.
            Your produce box delivery wasn’t made because the driver could not contact you or had a problem with your delivery instructions. Your box will be scheduled for the following week on the same day between 10 AM and 9 PM. Please, let us know if you have any issues with the delivery or if you would like to make changes to your delivery instructions.
            Thanks, and stay safe!
        """).strip()
        self.request.send_recipient_rescheduled_notification(api=self.api)
        self.api.send_text.assert_called_with(self.request.phone_number, expected, "groceries")

    def test_send_recipient_confirm_received_notification(self):
        expected = dedent("""
            Hello Ryan,
            This is a message from The People's Pantry.
            Can you confirm that you received your produce box on Monday March 15?
            Thank you!
        """).strip()
        self.request.send_recipient_confirm_received_notification(api=self.api)
        self.api.send_text.assert_called_with(self.request.phone_number, expected, "groceries")
