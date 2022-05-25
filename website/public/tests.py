from django.urls import reverse
from django.test import TestCase


class IndexViewTest(TestCase):
    def test_something(self):
        url = reverse("public:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Founded in response to COVID-19, we provide homecooked meals and grocery care packages to those struggling with food insecurity.",
        )
