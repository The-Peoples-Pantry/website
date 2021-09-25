from io import StringIO
from django.core.management import call_command
from django.test import TestCase, override_settings

from recipients.models import GroceryRequest
from recipients.factories import GroceryRequestFactory


@override_settings(GROCERIES_LIMIT=10)
class RunGroceryRequestCommandTests(TestCase):
    def call_run_grocery_request_lottery(self, **kwargs):
        """Invoke the command and return the output"""
        out = StringIO()
        call_command("run_grocery_request_lottery", stdout=out, **kwargs)
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
        eligible = GroceryRequestFactory.create_batch(
            20, status=GroceryRequest.Status.SUBMITTED
        )
        ineligible = GroceryRequestFactory.create_batch(
            80, status=GroceryRequest.Status.DELIVERED
        )
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

    def test_doesnt_perform_change_on_dry_run(self):
        requests = GroceryRequestFactory.create_batch(
            20, status=GroceryRequest.Status.SUBMITTED
        )
        self.call_run_grocery_request_lottery(dry_run=True)

        for request in requests:
            request.refresh_from_db()
            self.assertEqual(request.status, GroceryRequest.Status.SUBMITTED)
