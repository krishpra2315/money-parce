from django.urls import path
from . import views

app_name = 'goals'

urlpatterns = [
    path('', views.goal_list, name='goal_list'),
    path('create/', views.create_goal, name='create_goal'),
    path('contribute/<int:goal_id>/', views.contribute_to_goal, name='contribute_to_goal'),
    path('delete/<int:goal_id>/', views.delete_goal, name='delete_goal'),
] 