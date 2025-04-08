from django.db import models
from django.conf import settings

class Transaction(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Food'),
        ('entertainment', 'Entertainment'),
        ('shopping', 'Shopping'),
        ('transportation', 'Transportation'),
        ('subscriptions', 'Subscriptions'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.name} - ${self.amount}"
