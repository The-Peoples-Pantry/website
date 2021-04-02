from django.urls import path
from . import views

app_name = 'recipients'
urlpatterns = [
    path('', views.RequestIndexView.as_view(), name='index'),
    path('meal-request/new', views.MealRequestView.as_view(), name='new_meal_request'),
    path('grocery-request/new', views.GroceryRequestView.as_view(), name='new_grocery_request'),
    path('success', views.RequestSuccessView.as_view(), name='success'),
    path('<int:pk>/detail', views.MealRequestDetail.as_view(), name='request_detail')
]
