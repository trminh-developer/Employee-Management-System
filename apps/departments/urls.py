from django.urls import path
from . import views

app_name = 'departments'

urlpatterns = [
    path('', views.departments_list, name='list'),
]
