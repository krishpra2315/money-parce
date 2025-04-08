from django.urls import path
from . import views

urlpatterns = [
    path('', views.bill_reminders, name='bill_reminders'),
]
