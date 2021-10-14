from django.contrib.auth.models import Group, User


# Include in tests to add helpful methods
# eg.
#
# from django.test import TestCase
# from website.test_helper import TestHelper
#
# class MyFancyTest(TestHelper, TestCase):
#     def test_something(self):
#         self.with_user(groups=['Chefs'])
#         self.get(...)
#
class TestHelper:
    # Creates and logs in a user, optionally assigns them the named groups
    # eg. self.with_user(groups=["Chefs"])
    def with_user(self, groups=[]):
        user, _ = User.objects.get_or_create(
            username="test@example.com", password="test@example.com"
        )

        for group_name in groups:
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)

        self.client.force_login(user)
        return user
