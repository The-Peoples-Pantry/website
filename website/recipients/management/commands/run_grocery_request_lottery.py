from django.core.management.base import BaseCommand

from recipients.lottery import GroceryRequestLottery
from recipients.models import GroceryRequest


class Command(BaseCommand):
    help = "Run the lottery for MealRequests and report on the outcome"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Select from the lottery but don't apply changes",
        )

    def handle(self, *args, **options):
        lottery = GroceryRequestLottery()
        total_grocery_requests = GroceryRequest.objects.all()
        self.stdout.write(f"Total GroceryRequests: {total_grocery_requests.count()}")
        self.stdout.write(
            f"Eligible GroceryRequests: {lottery.eligible_requests().count()}"
        )
        self.stdout.write(f"Will select: {lottery.num_to_select()}")

        selected, not_selected = lottery.select(dry_run=options["dry_run"])
        selected_ids = tuple(sorted(request.id for request in selected))
        not_selected_ids = tuple(sorted(request.id for request in not_selected))
        self.stdout.write(f"Selected: {selected_ids}")
        self.stdout.write(f"Not selected: {not_selected_ids}")
