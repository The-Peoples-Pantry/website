import collections
import random
from django.conf import settings

from recipients.models import MealRequest


def random_sample_with_weight(population_weights, k):
    """
    Like random.sample but with weights, no replacements, no duplicates

    - random.sample with `counts` parameter doesn't work because it results in
      duplicates being selected
    - random.choices with `weights` parameter similarly has replacements
    - This approach uses allows weights and removes elements after they're chosen
      which avoids duplicates.
    - Slow and poorly optimized.
    """
    selected = []
    # Create a Counter from the population, assigning count by weight
    counter = collections.Counter(population_weights)
    for i in range(k):
        # Turn the Counter into a list for random selection from
        # The list will have n repetitions of an element with weight n
        choice = random.choice(list(counter.elements()))
        # When chosen, remove the element from the population
        # Effectively removes all repetitions of the element
        counter.pop(choice)
        # Add the chosen element to the selected list
        selected.append(choice)
    # Since selected elements have been removed from the population
    # what remains is the elements that weren't selected
    not_selected = list(counter.keys())
    return selected, not_selected


class MealRequestLottery:
    """Select/reject meal requests for fulfillment by our volunteers"""

    def __init__(self, k=None):
        self.k = k or settings.MEALS_LIMIT

    def already_selected(self):
        return MealRequest.objects.filter(status=MealRequest.Status.SELECTED)

    def eligible_requests(self):
        return MealRequest.objects.filter(status=MealRequest.Status.SUBMITTED)

    def num_to_select(self):
        return min(
            self.k - self.already_selected().count(),
            self.eligible_requests().count()
        )

    def candidates(self):
        return {
            request: request.get_lottery_weight()
            for request in self.eligible_requests()
        }

    def select(self):
        """Select k requests, reject the others, and mark each accordingly"""
        selected, not_selected = random_sample_with_weight(self.candidates(), self.num_to_select())
        self.__process_selected(selected)
        self.__process_not_selected(not_selected)
        return selected, not_selected

    def __process_selected(self, selected):
        for request in selected:
            request.status = MealRequest.Status.SELECTED
            request.send_lottery_selected_email()
            request.save()

    def __process_not_selected(self, not_selected):
        for request in not_selected:
            request.status = MealRequest.Status.NOT_SELECTED
            request.send_lottery_not_selected_email()
            request.save()
