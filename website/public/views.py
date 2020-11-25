from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.mixins import UserPassesTestMixin

def index(request):
    return render(request, "public/index.html")


class MapView():
    def google_maps_api_key(self):
        return settings.GOOGLE_MAPS_API_KEY

    def google_maps_embed_key(self):
        return settings.GOOGLE_MAPS_EMBED_KEY


class GroupView(UserPassesTestMixin):
    def test_func(self):

        return (self.request.user.groups.filter(name=self.permission_group).exists()
            or self.request.user.is_staff)

    def handle_no_permission(self):
        return redirect('/accounts/profile')
