from django.core.management.base import BaseCommand

from recipients.lottery import MealRequestLottery
from recipients.models import MealRequest


class Command(BaseCommand):
    # help = 'Closes the specified poll for voting'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        lottery = MealRequestLottery()
        total_meal_requests = MealRequest.objects.all()
        self.stdout.write(f"Total MealRequests: {total_meal_requests.count()}")
        self.stdout.write(f"Eligible MealRequests: {lottery.eligible_requests().count()}")
        self.stdout.write(f"Already Selected MealRequests: {lottery.already_selected().count()}")
        self.stdout.write(f"Will select: {lottery.num_to_select()}")

        selected, not_selected = lottery.select()
        selected_ids = tuple(sorted(request.id for request in selected))
        not_selected_ids = tuple(sorted(request.id for request in not_selected))
        self.stdout.write(f"Selected: {selected_ids}")
        self.stdout.write(f"Not selected: {not_selected_ids}")
