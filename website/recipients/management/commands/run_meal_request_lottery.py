from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipients.lottery import Lottery
from recipients.models import MealRequest, Status


class Command(BaseCommand):
    # help = 'Closes the specified poll for voting'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        total_meal_requests = MealRequest.objects.all()
        eligible_meal_requests = MealRequest.objects.filter(status=Status.SUBMITTED)
        already_selected_meal_requests = MealRequest.objects.filter(status=Status.SELECTED)
        num_to_choose = settings.MEALS_LIMIT - already_selected_meal_requests.count()
        self.stdout.write(f"Total MealRequests: {total_meal_requests.count()}")
        self.stdout.write(f"Eligible MealRequests: {eligible_meal_requests.count()}")
        self.stdout.write(f"Already Selected MealRequests: {already_selected_meal_requests.count()}")
        self.stdout.write(f"Will select: {num_to_choose}")

        lottery = Lottery(eligible_meal_requests, num_to_choose)
        lottery.select()
        # for poll_id in options['poll_ids']:
        #     try:
        #         poll = Poll.objects.get(pk=poll_id)
        #     except Poll.DoesNotExist:
        #         raise CommandError('Poll "%s" does not exist' % poll_id)

        #     poll.opened = False
        #     poll.save()

        #     self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))