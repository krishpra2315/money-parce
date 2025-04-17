from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.yearly_report, name='yearly_report'),
    path('download/', views.download_report_csv, name='download_report'),
    path('download/<int:year>/', views.download_report_csv, name='download_report_year'),
] 