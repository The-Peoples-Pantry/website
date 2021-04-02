from django.urls import path
from . import views

app_name = 'public'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('media', views.MediaView.as_view(), name='media'),
]
