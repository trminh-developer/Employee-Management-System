from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.employees_list, name='list'),
    path('api/', views.api_employees, name='api_list'),
    path('my-profile/', views.my_profile, name='my_profile'),
    path('<int:id>/', views.profile, name='profile'),
]
