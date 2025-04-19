from django.urls import path
from . import views

app_name = 'budgets'

urlpatterns = [
    path('', views.budget_dashboard, name='budget_dashboard'),
    path('budget/create/', views.create_budget, name='create_budget'),
    path('budget/<int:budget_id>/edit/', views.edit_budget, name='edit_budget'),
    path('budget/<int:budget_id>/delete/', views.delete_budget, name='delete_budget'),
] 