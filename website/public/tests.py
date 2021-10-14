from django.urls import reverse
from django.test import TestCase


class IndexViewTest(TestCase):
    def test_something(self):
        url = reverse("public:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "We provide home cooked meals and groceries to those who have been hit hardest by COVID-19",
        )
