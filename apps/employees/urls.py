from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.employees_list, name='list'),
    path('api/', views.api_employees, name='api_list'),
    path('search-api/', views.global_search, name='search_api'),
    path('my-profile/', views.my_profile, name='my_profile'),
    path('<int:id>/', views.profile, name='profile'),
]
