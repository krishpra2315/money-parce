from django.urls import path
from . import views

app_name = 'scholarships'

urlpatterns = [
    path('', views.scholarship_dashboard, name='dashboard'),
    path('delete/<int:scholarship_id>/', views.delete_scholarship, name='delete_scholarship'),
    path('api/data/', views.scholarship_data, name='api_data'),
] 