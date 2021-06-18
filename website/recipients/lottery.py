import random
from recipients.models import Status


class Lottery:
    """Select/reject submitted requests for fulfillment by our volunteers"""

    def __init__(self, requests, k):
        self.requests = requests
        self.k = min(k, len(self.requests))

    def select(self):
        """Select k requests, reject the others, and mark each accordingly"""
        selected = random.sample(self.requests, k=self.k)
        # TODO: Improve selection process to not be O(n^2)
        not_selected = [request for request in self.requests if request not in selected]

        for request in selected:
            request.status = Status.SELECTED
            request.save()

        for request in not_selected:
            request.status = Status.NOT_SELECTED
            request.save()

        return selected, not_selected
