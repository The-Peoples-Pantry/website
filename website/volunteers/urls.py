from django.urls import path
from . import views

app_name = 'volunteers'
urlpatterns = [
    path('chef-signup', views.ChefSignupListView.as_view(), name='chef_signup_list'),
    path('chef-signup/<int:pk>', views.ChefSignupView.as_view(), name='chef_signup'),
    path('chef-list', views.ChefTaskListView.as_view(), name='chef_list'),
    path('delivery-signup', views.DelivererSignupListView.as_view(), name='deliverer_signup_list'),
    path('delivery-signup/<int:pk>', views.DelivererSignupView.as_view(), name='deliverer_signup'),
    path('delivery-list', views.DelivererTaskListView.as_view(), name='deliverer_list'),

    path('chef-application', views.ChefApplicationView.as_view(), name='chef_application'),
    path('delivery-application', views.DelivererApplicationView.as_view(), name='deliverer_application'),
    path('organizer-application', views.OrganizerApplicationView.as_view(), name='organizer_application'),
    path('application-received', views.ApplicationReceivedView.as_view(), name='application_received'),
    path('resources', views.ResourcesView.as_view(), name='resources'),
]
