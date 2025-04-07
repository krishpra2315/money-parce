from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.transaction_list, name='transaction_list'),
    path('delete/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
] 