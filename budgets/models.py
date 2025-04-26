from django.db import models
from django.conf import settings
from django.db.models import Sum
from transactions.models import Transaction  # Import Transaction model to use its categories
from datetime import datetime
from decimal import Decimal # Import Decimal

class BudgetCategory(models.Model):
    name = models.CharField(max_length=100, choices=Transaction.CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_name_display()} - {self.user.username}"

class MonthlyBudget(models.Model):
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Automatically updated spent amount for this budget month.")
    month = models.DateField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ai_suggestion = models.TextField(blank=True, null=True, help_text="AI-generated suggestion for saving money in this category.")
    suggestion_generated = models.BooleanField(default=False, help_text="Indicates if an AI suggestion has been generated since crossing the threshold.")

    class Meta:
        unique_together = ['category', 'month', 'user']

    def __str__(self):
        return f"{self.category.name} - {self.month.strftime('%B %Y')} - {self.amount}"

    def get_spent_amount(self):
        return self.spent_amount

    def get_remaining_amount(self):
        return self.amount - self.spent_amount

    def get_progress_percentage(self):
        if self.amount is None or self.amount == Decimal('0.00'):
            return 100.0
        return float((self.spent_amount / self.amount) * 100) if self.amount else 100.0

    def get_alert_status(self):
        spent_percentage = self.get_progress_percentage()
        if spent_percentage >= 80:
            return {
                'alert': True,
                'message': f'You have used {spent_percentage:.1f}% of your {self.category.get_name_display()} budget!',
                'level': 'warning' if spent_percentage < 100 else 'danger'
            }
        return {'alert': False}

    @classmethod
    def get_current_alerts(cls, user):
        current_month = datetime.now().replace(day=1)
        budgets = cls.objects.filter(
            user=user,
            month__year=current_month.year,
            month__month=current_month.month
        )
        alerts = []
        for budget in budgets:
            status = budget.get_alert_status()
            if status['alert']:
                alerts.append(status)
        return alerts

    def check_and_reset_suggestion_flag(self):
        if self.suggestion_generated and self.get_progress_percentage() < 80:
            self.suggestion_generated = False
            self.ai_suggestion = None
            self.save(update_fields=['suggestion_generated', 'ai_suggestion']) 