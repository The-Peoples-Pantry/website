from django.urls import reverse
from django.test import TestCase

from website.test_helper import TestHelper


class ChefSignupListViewTest(TestHelper, TestCase):
    def test_something(self):
        self.with_user(groups=["Chefs"])
        url = reverse("volunteers:chef_signup_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Sign up to cook meals",
        )
