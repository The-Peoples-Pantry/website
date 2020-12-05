from django.shortcuts import render, redirect
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse

from core.models import has_group


def index(request):
    return render(request, "public/index.html")


class GroupView(UserPassesTestMixin):
    def test_func(self):
        return has_group(self.request.user, self.permission_group) or self.request.user.is_staff

    def get_permission_group_redirect_url(self):
        default = reverse('profile')
        return getattr(self, 'permission_group_redirect_url', default)

    def handle_no_permission(self):
        return redirect(self.get_permission_group_redirect_url())
