from io import StringIO
from django.core.management import call_command
from django.test import TestCase, override_settings

from recipients.models import GroceryRequest
from recipients.factories import GroceryRequestFactory


@override_settings(GROCERIES_LIMIT=10)
class RunGroceryRequestCommandTests(TestCase):
    def call_run_grocery_request_lottery(self):
        """Invoke the command and return the output"""
        out = StringIO()
        call_command("run_grocery_request_lottery", stdout=out)
        return out.getvalue()

    def test_runs_command(self):
        self.call_run_grocery_request_lottery()

    def test_writes_total_count(self):
        GroceryRequestFactory.create_batch(100)
        output = self.call_run_grocery_request_lottery()
        self.assertIn("Total GroceryRequests: 100", output)

    def test_writes_eligible_count(self):
        GroceryRequestFactory.create_batch(20, status=GroceryRequest.Status.SUBMITTED)
        GroceryRequestFactory.create_batch(80, status=GroceryRequest.Status.DELIVERED)
        output = self.call_run_grocery_request_lottery()
        self.assertIn("Total GroceryRequests: 100", output)
        self.assertIn("Eligible GroceryRequests: 20", output)

    def test_selects_from_eligible(self):
        eligible = GroceryRequestFactory.create_batch(20, status=GroceryRequest.Status.SUBMITTED)
        ineligible = GroceryRequestFactory.create_batch(80, status=GroceryRequest.Status.DELIVERED)
        self.call_run_grocery_request_lottery()

        selected, not_selected = [], []
        for request in eligible:
            request.refresh_from_db()
            if request.status == GroceryRequest.Status.SELECTED:
                selected.append(request)
            if request.status == GroceryRequest.Status.NOT_SELECTED:
                not_selected.append(request)

        for request in [*selected, *not_selected]:
            self.assertIn(request, eligible)
            self.assertNotIn(request, ineligible)

    def test_selects_only_up_to_limit(self):
        """If we have a limit of 10 and 8 are already selected, select 2"""
        eligible = GroceryRequestFactory.create_batch(20, num_adults=1, status=GroceryRequest.Status.SUBMITTED)
        GroceryRequestFactory.create_batch(8, num_adults=1, status=GroceryRequest.Status.SELECTED)
        output = self.call_run_grocery_request_lottery()
        self.assertIn("Already Selected GroceryRequests: 8", output)
        self.assertIn("Will select: 2", output)

        newly_selected = []
        for request in eligible:
            request.refresh_from_db()
            if request.status == GroceryRequest.Status.SELECTED:
                newly_selected.append(request)
        self.assertEqual(2, len(newly_selected))
