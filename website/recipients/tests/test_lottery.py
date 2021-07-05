import datetime
import textwrap
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from recipients.factories import MealRequestFactory, GroceryRequestFactory
from recipients.lottery import MealRequestLottery, GroceryRequestLottery
from recipients.models import MealRequest, GroceryRequest


class AssertionMixin(TestCase):
    """Helper assertions for lottery tests"""
    def assertMoreLikely(self, a, b, selected):
        """Asserts that it is more likely to select from group a than group b"""
        self.assertGreater(
            len(set(a).intersection(set(selected))),
            len(set(b).intersection(set(selected))),
            "Expected to select more values from group a than group b but it did not",
        )

    def assertEmailSent(self, subject, recipient):
        """Asserts that email was sent to the recipient with the given subject"""
        has_match = any(
            (email.subject == subject) and (recipient in email.to)
            for email in mail.outbox
        )
        self.assertTrue(has_match, textwrap.dedent(
            f"""
            Expected an email to have been sent to `{recipient}` with subject: `{subject}`
            No emails in the outbox matched
            There were {len(mail.outbox)} emails in the outbox
            """)
        )

    def assertEmailNotSent(self, subject, recipient):
        """Asserts that email was not sent to the recipient with the given subject"""
        has_match = any(
            (email.subject == subject) and (recipient in email.to)
            for email in mail.outbox
        )
        self.assertFalse(has_match, textwrap.dedent(
            f"""
            Expected an email not to have been sent to `{recipient}` with subject: `{subject}`
            A matching email was found in the outbox
            There were {len(mail.outbox)} emails in the outbox
            """)
        )


class MealRequestLotteryTests(AssertionMixin, TestCase):
    def test_result_selects_correct_number(self):
        MealRequestFactory.create_batch(50, status=MealRequest.Status.SUBMITTED)
        selected, not_selected = MealRequestLottery(10).select()

        self.assertEqual(len(selected), 10)
        self.assertEqual(len(not_selected), 40)

    def test_results_marked_selected_and_not_selected(self):
        MealRequestFactory.create_batch(50, status=MealRequest.Status.SUBMITTED)
        selected, not_selected = MealRequestLottery(10).select()

        for request in selected:
            self.assertEqual(request.status, MealRequest.Status.SELECTED)
        for request in not_selected:
            self.assertEqual(request.status, MealRequest.Status.NOT_SELECTED)

    def test_results_send_emails_to_correct_recipients(self):
        MealRequestFactory.create_batch(50, status=MealRequest.Status.SUBMITTED)
        selected, not_selected = MealRequestLottery(10).select()

        for request in selected:
            self.assertEmailSent(
                "Your meal request for The People's Pantry has been selected",
                request.email
            )
            self.assertEmailNotSent(
                "Your meal request for The People's Pantry was not selected",
                request.email
            )
        for request in not_selected:
            self.assertEmailSent(
                "Your meal request for The People's Pantry was not selected",
                request.email
            )
            self.assertEmailNotSent(
                "Your meal request for The People's Pantry has been selected",
                request.email
            )

    def test_results_are_randomized(self):
        # Run the lottery several times and make sure we get more than 1 order of results
        # Not a true test of randomness, but works well enough for our purpose here
        results = set()
        for x in range(10):
            MealRequestFactory.create_batch(50, status=MealRequest.Status.SUBMITTED)
            lottery = MealRequestLottery(10)
            selected, _ = lottery.select()
            selected_ids = tuple(sorted(request.id for request in selected))
            results.add(selected_ids)
            MealRequest.objects.all().delete()
        self.assertGreater(len(results), 1)

    def test_results_do_not_repeat(self):
        MealRequestFactory.create_batch(50, status=MealRequest.Status.SUBMITTED)
        selected, not_selected = MealRequestLottery(10).select()

        self.assertEqual(len(set(selected)), len(selected))
        self.assertEqual(len(set(not_selected)), len(not_selected))

    def test_results_cant_be_both_selected_and_not_selected(self):
        MealRequestFactory.create_batch(50, status=MealRequest.Status.SUBMITTED)
        selected, not_selected = MealRequestLottery(10).select()
        selected_ids = set(request.id for request in selected)
        not_selected_ids = set(request.id for request in not_selected)

        self.assertTrue(selected_ids.isdisjoint(not_selected_ids))

    def test_selects_all_if_selection_size_is_larger_than_requests(self):
        MealRequestFactory.create_batch(50, status=MealRequest.Status.SUBMITTED)
        selected, not_selected = MealRequestLottery(60).select()

        self.assertEqual(len(selected), 50)
        self.assertEqual(len(not_selected), 0)

    def test_gives_additional_weight_to_demographics(self):
        """Requests any of our supported demographics should have additional weight"""
        demographic_meal_requests = MealRequestFactory.create_batch(100, bipoc=True)  # Or any other demographic
        non_demographic_meal_requests = MealRequestFactory.create_batch(
            100,
            **{demographic: False for demographic in MealRequest.DEMOGRAPHIC_ATTRIBUTES},
        )
        selected, _ = MealRequestLottery(100).select()

        self.assertMoreLikely(demographic_meal_requests, non_demographic_meal_requests, selected)

    def test_gives_additional_weight_to_previously_not_selected(self):
        """Requests from folks that were previously not selected should have additional weight"""
        has_previous_unselected_requests = [MealRequestFactory(phone_number=f"555555555{i}") for i in range(100)]
        no_previous_unselected_requests = [MealRequestFactory(phone_number=f"444444444{i}") for i in range(100)]

        # Add previously unselected requests
        for request in has_previous_unselected_requests:
            for previous_request in MealRequestFactory.create_batch(5, phone_number=request.phone_number, status=MealRequest.Status.NOT_SELECTED):
                previous_request.created_at = timezone.now() - datetime.timedelta(days=1)
                previous_request.save()

        selected, _ = MealRequestLottery(100).select()

        self.assertMoreLikely(has_previous_unselected_requests, no_previous_unselected_requests, selected)


class GroceryRequestLotteryTests(AssertionMixin, TestCase):
    def test_result_selects_correct_number_when_all_requests_get_one_box(self):
        # When every request is eligible for exactly one box its easy to select the correct number of boxes - its the same as the number of requests
        GroceryRequestFactory.create_batch(50, num_adults=1, status=GroceryRequest.Status.SUBMITTED)
        selected, not_selected = GroceryRequestLottery(10).select()
        num_boxes_selected = sum(request.boxes for request in selected)

        self.assertEqual(num_boxes_selected, 10)
        self.assertEqual(len(selected), 10)

    def test_results_marked_selected_and_not_selected(self):
        GroceryRequestFactory.create_batch(50, status=GroceryRequest.Status.SUBMITTED)
        selected, not_selected = GroceryRequestLottery(10).select()

        for request in selected:
            self.assertEqual(request.status, GroceryRequest.Status.SELECTED)
        for request in not_selected:
            self.assertEqual(request.status, GroceryRequest.Status.NOT_SELECTED)

    def test_result_selects_correct_number_when_they_do_not_add_up_to_exact_limit(self):
        # When all requests are for a number of boxes that the limit isn't evenly divisible by we can't select the exact limit
        # eg. if we're selecting 10 boxes but every request is for 3 boxes. 10 isn't evenly divisible by 3, so we'd select 9 instead
        # When number of adults is > 7 we give 3 boxes
        GroceryRequestFactory.create_batch(50, num_adults=10, status=GroceryRequest.Status.SUBMITTED)
        selected, not_selected = GroceryRequestLottery(10).select()
        num_boxes_selected = sum(request.boxes for request in selected)

        self.assertEqual(num_boxes_selected, 9)
        self.assertEqual(len(selected), 3)

    def test_never_exceeds_limit(self):
        # Slightly random test
        # When not given an explicit num_adults (to determine the number of boxes) assert that it nevertheless comes in within the limit
        for i in range(10):
            GroceryRequestFactory.create_batch(50, status=GroceryRequest.Status.SUBMITTED)
            selected, not_selected = GroceryRequestLottery(10).select()
            num_boxes_selected = sum(request.boxes for request in selected)
            self.assertLessEqual(num_boxes_selected, 10)
            self.assertGreaterEqual(num_boxes_selected, 10 - 2)
            self.assertLessEqual(len(selected), 10)
            self.assertGreater(len(selected), 0)
            GroceryRequest.objects.all().delete()

    def test_results_are_randomized(self):
        # Run the lottery several times and make sure we get more than 1 order of results
        # Not a true test of randomness, but works well enough for our purpose here
        results = set()
        for x in range(10):
            GroceryRequestFactory.create_batch(50, status=GroceryRequest.Status.SUBMITTED)
            lottery = GroceryRequestLottery(10)
            selected, _ = lottery.select()
            selected_ids = tuple(sorted(request.id for request in selected))
            results.add(selected_ids)
            GroceryRequest.objects.all().delete()
        self.assertGreater(len(results), 1)

    def test_results_do_not_repeat(self):
        GroceryRequestFactory.create_batch(50, status=GroceryRequest.Status.SUBMITTED)
        selected, not_selected = GroceryRequestLottery(10).select()

        self.assertEqual(len(set(selected)), len(selected))
        self.assertEqual(len(set(not_selected)), len(not_selected))

    def test_results_cant_be_both_selected_and_not_selected(self):
        GroceryRequestFactory.create_batch(50, status=GroceryRequest.Status.SUBMITTED)
        selected, not_selected = GroceryRequestLottery(10).select()
        selected_ids = set(request.id for request in selected)
        not_selected_ids = set(request.id for request in not_selected)

        self.assertTrue(selected_ids.isdisjoint(not_selected_ids))

    def test_selects_all_if_selection_size_is_larger_than_requests(self):
        GroceryRequestFactory.create_batch(50, num_adults=1, status=GroceryRequest.Status.SUBMITTED)
        selected, not_selected = GroceryRequestLottery(60).select()

        self.assertEqual(len(selected), 50)
        self.assertEqual(len(not_selected), 0)

    def test_gives_additional_weight_to_demographics(self):
        """Requests any of our supported demographics should have additional weight"""
        demographic_grocery_requests = GroceryRequestFactory.create_batch(100, bipoc=True)  # Or any other demographic
        non_demographic_grocery_requests = GroceryRequestFactory.create_batch(
            100,
            **{demographic: False for demographic in GroceryRequest.DEMOGRAPHIC_ATTRIBUTES},
        )
        selected, _ = GroceryRequestLottery(100).select()

        self.assertMoreLikely(demographic_grocery_requests, non_demographic_grocery_requests, selected)

    def test_gives_additional_weight_to_previously_not_selected(self):
        """Requests from folks that were previously not selected should have additional weight"""
        has_previous_unselected_requests = [GroceryRequestFactory(phone_number=f"555555555{i}") for i in range(100)]
        no_previous_unselected_requests = [GroceryRequestFactory(phone_number=f"444444444{i}") for i in range(100)]

        # Add previously unselected requests
        for request in has_previous_unselected_requests:
            for previous_request in GroceryRequestFactory.create_batch(5, phone_number=request.phone_number, status=GroceryRequest.Status.NOT_SELECTED):
                previous_request.created_at = timezone.now() - datetime.timedelta(days=1)
                previous_request.save()

        selected, _ = GroceryRequestLottery(100).select()

        self.assertMoreLikely(has_previous_unselected_requests, no_previous_unselected_requests, selected)