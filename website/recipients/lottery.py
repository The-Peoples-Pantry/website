import collections
import random
from recipients.models import Status


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


class Lottery:
    """Select/reject submitted requests for fulfillment by our volunteers"""

    def __init__(self, requests, k):
        self.requests = requests
        self.k = min(k, len(self.requests))

    def select(self):
        """Select k requests, reject the others, and mark each accordingly"""
        population_weights = {
            request: request.get_lottery_weight()
            for request in self.requests
        }
        selected, not_selected = random_sample_with_weight(population_weights, self.k)

        for request in selected:
            request.status = Status.SELECTED
            request.save()

        for request in not_selected:
            request.status = Status.NOT_SELECTED
            request.save()

        return selected, not_selected
