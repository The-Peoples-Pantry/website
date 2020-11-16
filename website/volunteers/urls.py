from django.urls import path
from . import views

app_name = 'volunteers'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('chef-signup', views.ChefSignupView.as_view(), name='chef_signup'),
    path('chef-list', views.ChefIndexView.as_view(), name='chef_list'),
    path('delivery-signup', views.DeliverySignupView.as_view(), name='chef_signup'),
    path('delivery-list', views.DeliveryIndexView.as_view(), name='chef_signup')
]