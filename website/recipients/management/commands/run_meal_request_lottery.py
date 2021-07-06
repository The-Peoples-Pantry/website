from django.core.management.base import BaseCommand

from recipients.lottery import MealRequestLottery
from recipients.models import MealRequest


class Command(BaseCommand):
    help = 'Run the lottery for MealRequests and report on the outcome'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help="Select from the lottery but don't apply changes")

    def handle(self, *args, **options):
        lottery = MealRequestLottery()
        total_meal_requests = MealRequest.objects.all()
        self.stdout.write(f"Total MealRequests: {total_meal_requests.count()}")
        self.stdout.write(f"Eligible MealRequests: {lottery.eligible_requests().count()}")
        self.stdout.write(f"Already Selected MealRequests: {lottery.already_selected().count()}")
        self.stdout.write(f"Will select: {lottery.num_to_select()}")

        selected, not_selected = lottery.select(dry_run=options['dry_run'])
        selected_ids = tuple(sorted(request.id for request in selected))
        not_selected_ids = tuple(sorted(request.id for request in not_selected))
        self.stdout.write(f"Selected: {selected_ids}")
        self.stdout.write(f"Not selected: {not_selected_ids}")
