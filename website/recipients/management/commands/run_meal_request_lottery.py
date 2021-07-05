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

        lottery.select()
        # for poll_id in options['poll_ids']:
        #     try:
        #         poll = Poll.objects.get(pk=poll_id)
        #     except Poll.DoesNotExist:
        #         raise CommandError('Poll "%s" does not exist' % poll_id)

        #     poll.opened = False
        #     poll.save()

        #     self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
