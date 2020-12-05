from django.shortcuts import render, redirect
from django.contrib.auth.mixins import UserPassesTestMixin


def index(request):
    return render(request, "public/index.html")


class GroupView(UserPassesTestMixin):
    def test_func(self):
        has_group = self.request.user.groups.filter(name=self.permission_group).exists()
        return has_group or self.request.user.is_staff

    def handle_no_permission(self):
        return redirect('/accounts/profile')
