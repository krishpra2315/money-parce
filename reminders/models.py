from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

class BillReminder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def is_due_soon(self):
        return self.due_date >= timezone.now().date() and not self.is_paid

    def __str__(self):
        return f"{self.title} - Due {self.due_date}"
