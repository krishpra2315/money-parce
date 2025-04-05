from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User
from .forms import UserRegistrationForm

class UserAdmin(BaseUserAdmin):
    """Define admin model for custom User model with email instead of username."""
    
    add_form = UserRegistrationForm
    list_display = ('email', 'name', 'age', 'bank_linked', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'bank_linked')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name', 'age', 'bank_linked')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'age', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'name')
    ordering = ('email',)

admin.site.register(User, UserAdmin)
