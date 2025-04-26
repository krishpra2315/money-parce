from django.urls import path
from . import views

app_name = 'savings'

urlpatterns = [
    path('', views.contribution_list, name='contribution_list'),
    path('create/', views.create_contribution, name='create_contribution'),
    path('delete/<int:contribution_id>/', views.delete_contribution, name='delete_contribution'),
    path('income-sources/<int:contribution_id>/', views.contribution_income_sources, name='contribution_income_sources'),
] 