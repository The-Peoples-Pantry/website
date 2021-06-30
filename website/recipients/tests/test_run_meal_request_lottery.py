from io import StringIO
from django.core.management import call_command
from django.test import TestCase, override_settings

from recipients.models import MealRequest, Status
from recipients.factories import MealRequestFactory


@override_settings(MEALS_LIMIT=10)
class RunMealRequestCommandTests(TestCase):
    def call_run_meal_request_lottery(self):
        """Invoke the command and return the output"""
        out = StringIO()
        call_command("run_meal_request_lottery", stdout=out)
        return out.getvalue()

    def test_runs_command(self):
        self.call_run_meal_request_lottery()

    def test_writes_total_count(self):
        MealRequestFactory.create_batch(100)
        output = self.call_run_meal_request_lottery()
        self.assertIn("Total MealRequests: 100", output)

    def test_writes_eligible_count(self):
        MealRequestFactory.create_batch(20, status=Status.SUBMITTED)
        MealRequestFactory.create_batch(80, status=Status.DELIVERED)
        output = self.call_run_meal_request_lottery()
        self.assertIn("Total MealRequests: 100", output)
        self.assertIn("Eligible MealRequests: 20", output)

    def test_selects_from_eligible(self):
        eligible = MealRequestFactory.create_batch(20, status=Status.SUBMITTED)
        ineligible = MealRequestFactory.create_batch(80, status=Status.DELIVERED)
        self.call_run_meal_request_lottery()

        selected, not_selected = [], []
        for request in eligible:
            request.refresh_from_db()
            if request.status == Status.SELECTED:
                selected.append(request)
            if request.status == Status.NOT_SELECTED:
                not_selected.append(request)
        self.assertEqual(10, len(selected))
        self.assertEqual(10, len(not_selected))

        for request in [*selected, *not_selected]:
            self.assertIn(request, eligible)
            self.assertNotIn(request, ineligible)

    def test_selects_only_up_to_limit(self):
        """If we have a limit of 10 and 8 are already selected, select 2"""
        eligible = MealRequestFactory.create_batch(20, status=Status.SUBMITTED)
        MealRequestFactory.create_batch(8, status=Status.SELECTED)
        output = self.call_run_meal_request_lottery()
        self.assertIn("Already Selected MealRequests: 8", output)
        self.assertIn("Will select: 2", output)

        newly_selected = []
        for request in eligible:
            request.refresh_from_db()
            if request.status == Status.SELECTED:
                newly_selected.append(request)
        self.assertEqual(2, len(newly_selected))
