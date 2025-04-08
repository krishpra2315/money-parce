from django.urls import path
from .views import (
    bill_reminders,
    BillReminderCreateView,
    BillReminderUpdateView,
    BillReminderDeleteView
)

urlpatterns = [
    path('', bill_reminders, name='bill_reminders'),
    path('new/', BillReminderCreateView.as_view(), name='reminder_create'),
    path('<int:pk>/edit/', BillReminderUpdateView.as_view(), name='reminder_edit'),
    path('<int:pk>/delete/', BillReminderDeleteView.as_view(), name='reminder_delete'),
]
