from django.urls import path
from . import views

app_name = 'volunteers'
urlpatterns = [
    path('application-received', views.ApplicationReceivedView.as_view(), name='application_received'),
    path('chef-application', views.ChefApplicationView.as_view(), name='chef_application'),
    path('chef-signup', views.ChefSignupListView.as_view(), name='chef_signup_list'),
    path('chef-signup/<int:pk>', views.ChefSignupView.as_view(), name='chef_signup'),
    path('chef-list', views.ChefTaskListView.as_view(), name='chef_list'),
    path('delivery-application', views.DeliveryApplicationView.as_view(), name='delivery_application'),
    path('delivery-signup', views.DelivererSignupListView.as_view(), name='delivery_signup_list'),
    path('delivery-signup/<int:pk>', views.DelivererSignupView.as_view(), name='delivery_signup'),
    path('delivery-list', views.DelivererTaskListView.as_view(), name='delivery_list'),
    path('organizer-application', views.OrganizerApplicationView.as_view(), name='organizer_application'),
    path('resources', views.ResourcesView.as_view(), name='resources'),
]
