from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class UserManager(BaseUserManager):
    """Define a model manager for User model with email as the unique identifier."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom User model with email as the unique identifier instead of username."""
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField(null=True, blank=True)
    bank_linked = models.BooleanField(default=False)
    daily_tip = models.TextField(null=True, blank=True, help_text="Stores the daily financial tip.")
    last_tip_date = models.DateField(null=True, blank=True, help_text="The date the last daily tip was generated.")

    # Plaid Integration Fields
    plaid_access_token = models.CharField(max_length=255, null=True, blank=True, help_text="Plaid access token for the user")
    plaid_item_id = models.CharField(max_length=255, null=True, blank=True, help_text="Plaid item ID for the user")
    plaid_institution_name = models.CharField(max_length=255, null=True, blank=True, help_text="Name of the institution linked via Plaid")
    plaid_sync_cursor = models.CharField(max_length=255, null=True, blank=True, help_text="Cursor for the next Plaid transaction sync")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def __str__(self):
        return self.email
