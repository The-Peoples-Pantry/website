from datetime import date
from django.test import TestCase
from textwrap import dedent
from unittest.mock import MagicMock

from recipients.factories import GroceryRequestFactory


class GroceryRequestTextTests(TestCase):
    def setUp(self):
        self.api = MagicMock()
        self.request = GroceryRequestFactory(
            name="Ryan",
            can_receive_texts=True,
            delivery_date=date.fromisoformat("2021-03-15"),
        )

    def test_send_recipient_scheduled_notification(self):
        expected = dedent(
            """
            Hi Ryan,
            This is a message from The People's Pantry.
            Your delivery has been scheduled for Monday March 15. FoodShare will be delivering your box between 10 AM and 9 PM at your door and/or following your delivery instructions. Please make sure to check your phone regularly so the delivery driver can communicate with you easily.
            Delivery dates may vary to balance daily orders or if the driver did not get to the delivery by 9 PM. If there are any changes, we will do our best to communicate with you ahead of time.
            Thank you and stay safe!

            Reply STOP to unsubscribe
        """
        ).strip()
        self.request.send_recipient_scheduled_notification(api=self.api)
        self.api.send_text.assert_called_with(
            self.request.phone_number, expected, "groceries"
        )

    def test_send_recipient_allergy_notification(self):
        expected = dedent(
            """
            Hi Ryan,
            This is a message from The People's Pantry.
            The FoodShare boxes this week included a food which you listed as an allergy, please let us know if you would like to cancel the box.
            Please feel free to be in touch with any questions, comments, or concerns.
        """
        ).strip()
        self.request.send_recipient_allergy_notification(api=self.api)
        self.api.send_text.assert_called_with(
            self.request.phone_number, expected, "groceries"
        )

    def test_send_recipient_reminder_notification(self):
        expected = dedent(
            """
            Hello Ryan,
            This is a message from The People's Pantry.
            Your FoodShare produce box is scheduled to be delivered today. Just a reminder that boxes are delivered until 9 PM. Please let us know once you receive your grocery box.
            If you don’t receive your box by that time today, please let us know by replying to this message, and we will reach out to FoodShare to see if a redelivery is possible.
            Thanks, and stay safe!
        """
        ).strip()
        self.request.send_recipient_reminder_notification(api=self.api)
        self.api.send_text.assert_called_with(
            self.request.phone_number, expected, "groceries"
        )

    def test_send_recipient_rescheduled_notification(self):
        expected = dedent(
            """
            Hello Ryan,
            This is a message from The People's Pantry.
            Your produce box delivery wasn’t made because the driver could not contact you or had a problem with your delivery instructions. Your box will be scheduled for the following week on the same day between 10 AM and 9 PM. Please, let us know if you have any issues with the delivery or if you would like to make changes to your delivery instructions.
            Thanks, and stay safe!
        """
        ).strip()
        self.request.send_recipient_rescheduled_notification(api=self.api)
        self.api.send_text.assert_called_with(
            self.request.phone_number, expected, "groceries"
        )

    def test_send_recipient_confirm_received_notification(self):
        expected = dedent(
            """
            Hello Ryan,
            This is a message from The People's Pantry.
            Can you confirm that you received your produce box on Monday March 15?
            Thank you!
        """
        ).strip()
        self.request.send_recipient_confirm_received_notification(api=self.api)
        self.api.send_text.assert_called_with(
            self.request.phone_number, expected, "groceries"
        )
