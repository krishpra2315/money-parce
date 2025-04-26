"""
URL configuration for moneyparce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
# Import include for the two_factor urls
from two_factor.urls import urlpatterns as tf_urls
# Import views from the users app
from users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include two_factor urls under '/account/'
    # Using 'account/' means URLs like /account/login/, /account/two_factor/setup/, etc.
    path('account/', include(tf_urls)),
    # Keep your app urls, but make sure they don't conflict with two_factor urls
    # Note: The login URL is now 'two_factor:login' which resolves to /account/login/
    path('users/', include('users.urls')),
    path('transactions/', include('transactions.urls', namespace='transactions')),
    path('goals/', include('goals.urls', namespace='goals')),
    path('budgets/', include('budgets.urls', namespace='budgets')),
    path('savings/', include('savings.urls', namespace='savings')),
    # This root path now correctly points to your home_view first
    path('', user_views.home_view, name='home'),
    path('reminders/', include('reminders.urls')),
    path('scholarships/', include('scholarships.urls', namespace='scholarships')),
    path('charts/', include('charts.urls', namespace='charts')),
    path('reports/', include('reports.urls', namespace='reports')),
]
