from django.db import models
from django.conf import settings
from transactions.models import Transaction  # Import Transaction model to use its categories

class BudgetCategory(models.Model):
    name = models.CharField(max_length=100, choices=Transaction.CATEGORY_CHOICES)  # Use same choices
    description = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_name_display()} - {self.user.username}"  # Use get_name_display() to show readable category name

class MonthlyBudget(models.Model):
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['category', 'month', 'user']

    def __str__(self):
        return f"{self.category.name} - {self.month.strftime('%B %Y')} - {self.amount}" 