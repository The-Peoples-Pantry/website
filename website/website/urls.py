"""website URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.urls import include, path

from core.views import UserCreationView

urlpatterns = [
    path('', include('public.urls')),
    path('signup', UserCreationView.as_view(), name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
    # login redirects to accounts/profile on successful login
    path('accounts/profile/', RedirectView.as_view(pattern_name='volunteers:index'), name='profile'),
    path('admin/', admin.site.urls),
    path('recipients/', include('recipients.urls')),
    path('volunteers/', include('volunteers.urls')),
]
