import statistics
from django.test import TestCase

from recipients.factories import MealRequestFactory
from recipients.lottery import Lottery
from recipients.models import MealRequest, Status


class LotteryTests(TestCase):
    def test_results_marked_selected_and_not_selected(self):
        meal_requests = MealRequestFactory.create_batch(50, status=Status.SUBMITTED)
        selected, not_selected = Lottery(meal_requests, 10).select()

        self.assertEqual(len(selected), 10)
        self.assertEqual(len(not_selected), 40)
        for request in selected:
            self.assertEqual(request.status, Status.SELECTED)
        for request in not_selected:
            self.assertEqual(request.status, Status.NOT_SELECTED)

    def test_results_are_randomized(self):
        meal_requests = MealRequestFactory.create_batch(50, status=Status.SUBMITTED)
        lottery = Lottery(meal_requests, 10)

        # Run the lottery several times and make sure we get more than 1 order of results
        # Not a true test of randomness, but works well enough for our purpose here
        results = set()
        for x in range(10):
            selected, _ = lottery.select()
            selected_ids = tuple(sorted(request.id for request in selected))
            results.add(selected_ids)
        self.assertGreater(len(results), 1)

    def test_results_do_not_repeat(self):
        meal_requests = MealRequestFactory.create_batch(50, status=Status.SUBMITTED)
        selected, not_selected = Lottery(meal_requests, 10).select()
        selected_ids = set(request.id for request in selected)
        not_selected_ids = set(request.id for request in not_selected)

        self.assertEqual(len(selected_ids), 10)
        self.assertEqual(len(not_selected_ids), 40)

    def test_results_cant_be_both_selected_and_not_selected(self):
        meal_requests = MealRequestFactory.create_batch(50, status=Status.SUBMITTED)
        selected, not_selected = Lottery(meal_requests, 10).select()
        selected_ids = set(request.id for request in selected)
        not_selected_ids = set(request.id for request in not_selected)

        self.assertTrue(selected_ids.isdisjoint(not_selected_ids))

    def test_selects_all_if_selection_size_is_larger_than_requests(self):
        meal_requests = MealRequestFactory.create_batch(50, status=Status.SUBMITTED)
        selected, not_selected = Lottery(meal_requests, 60).select()

        self.assertEqual(len(selected), 50)
        self.assertEqual(len(not_selected), 0)

    def test_gives_additional_weight_to_demographics(self):
        """Requests any of our supported demographics should have additional weight"""
        demographic_meal_requests = MealRequestFactory.create_batch(25, bipoc=True)  # Or any other demographic
        non_demographic_meal_requests = MealRequestFactory.create_batch(
            25,
            **{demographic: False for demographic in MealRequest.DEMOGRAPHIC_ATTRIBUTES},
        )
        meal_requests = demographic_meal_requests + non_demographic_meal_requests
        lottery = Lottery(meal_requests, 10)

        self.assertMoreLikely(demographic_meal_requests, non_demographic_meal_requests, lottery)

    def assertMoreLikely(self, group_a, group_b, lottery):
        """Asserts that it is more likely to select from group_a than group_b"""
        NUM_TEST_RUNS_FOR_STATISTICAL_SIGNIFICANCE = 30  # Arbitrary
        group_a_results = []
        group_b_results = []
        for x in range(NUM_TEST_RUNS_FOR_STATISTICAL_SIGNIFICANCE):
            selected, _ = lottery.select()
            group_a_selected = set(selected).intersection(set(group_a))
            group_a_results.append(len(group_a_selected))
            group_b_selected = set(selected).intersection(set(group_b))
            group_b_results.append(len(group_b_selected))

        group_a_mean_selections = statistics.mean(group_a_results)
        group_b_mean_selections = statistics.mean(group_b_results)
        self.assertGreater(
            group_a_mean_selections,
            group_b_mean_selections,
            "Expected it to be more likely to select from group A than group B but it wasn't"
        )
