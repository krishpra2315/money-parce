from django.db import models
from django.core.validators import MinValueValidator
from users.models import User

class Scholarship(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scholarships')
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - ${self.amount}"

class CollegeDebt(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='college_debt')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    
    def __str__(self):
        return f"College Debt for {self.user.email}: ${self.total_amount}"
    
    def scholarship_coverage_percentage(self):
        # Calculate what percentage of debt is covered by scholarships
        scholarships_total = self.user.scholarships.aggregate(
            total=models.Sum('amount'))['total'] or 0
        
        if self.total_amount == 0:
            return 100  # If no debt, consider it 100% covered
        
        coverage = (scholarships_total / self.total_amount) * 100
        return min(coverage, 100)  # Cap at 100%
