from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Transaction(models.Model):
    CATEGORY_CHOICES = [
        ('food', _('Food')),
        ('entertainment', _('Entertainment')),
        ('shopping', _('Shopping')),
        ('transportation', _('Transportation')),
        ('subscriptions', _('Subscriptions')),
        ('housing', _('Housing')),
        ('utilities', _('Utilities')),
        ('healthcare', _('Healthcare')),
        ('income', _('Income')),
        ('personal_care', _('Personal Care')),
        ('travel', _('Travel')),
        ('education', _('Education')),
        ('gifts_donations', _('Gifts/Donations')),
        ('other', _('Other')),
    ]
    TRANSACTION_TYPE_CHOICES = [
        ('expense', _('Expense')),
        ('income', _('Income')),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Always positive value")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, default='expense')
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='other')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Plaid specific fields
    plaid_transaction_id = models.CharField(max_length=255, unique=True, null=True, blank=True, help_text="Unique ID from Plaid for this transaction")
    plaid_account_id = models.CharField(max_length=255, null=True, blank=True, help_text="Account ID from Plaid")
    pending = models.BooleanField(default=False, help_text="Whether the transaction is still pending")

    class Meta:
        ordering = ['-date', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'plaid_transaction_id'], name='unique_user_plaid_transaction')
        ]

    def __str__(self):
        status = "[PENDING] " if self.pending else ""
        type_indicator = "(-)" if self.transaction_type == 'expense' else "(+)"
        return f"{status}{self.name} {type_indicator} ({self.category}) - ${self.amount} on {self.date}"
