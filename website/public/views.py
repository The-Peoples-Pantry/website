from django.shortcuts import render, redirect
from django.contrib.auth.mixins import UserPassesTestMixin

from core.models import has_group


def index(request):
    return render(request, "public/index.html")


class GroupView(UserPassesTestMixin):
    def test_func(self):
        return has_group(self.request.user, self.permission_group) or self.request.user.is_staff

    def handle_no_permission(self):
        return redirect('/accounts/profile')
