from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Plaid Integration URLs
    path('plaid/create_link_token/', views.create_link_token_view, name='create_link_token'),
    path('plaid/exchange_public_token/', views.exchange_public_token_view, name='exchange_public_token'),
    path('plaid/manage/', views.manage_plaid_connection_view, name='manage_plaid_connection'),
    path('plaid/remove/', views.remove_plaid_connection_view, name='remove_plaid_connection'),
] 