from django.urls import path
from . import views

app_name = 'recipients'
urlpatterns = [
    path('', views.index, name='index'),
    path('meal-request/new', views.MealRequestView.as_view(), name='new_meal_request'),
    path('success', views.success, name='success'),
    path('<int:pk>/detail', views.MealRequestDetail.as_view(), name='request_detail')
]
