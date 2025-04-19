from django import forms
from .models import BudgetCategory, MonthlyBudget
from django.contrib.auth.models import User
from transactions.models import Transaction
from datetime import datetime

class BudgetCategoryForm(forms.ModelForm):
    class Meta:
        model = BudgetCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MonthlyBudgetForm(forms.ModelForm):
    month = forms.CharField(widget=forms.DateInput(attrs={
        'class': 'form-control',
        'type': 'month'
    }))

    class Meta:
        model = MonthlyBudget
        fields = ['category', 'amount', 'month']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, user, *args, **kwargs):
        super(MonthlyBudgetForm, self).__init__(*args, **kwargs)
        # Get or create budget categories for each transaction category
        for category_code, category_name in Transaction.CATEGORY_CHOICES:
            BudgetCategory.objects.get_or_create(
                user=user,
                name=category_code,
                defaults={'description': category_name}
            )
        self.fields['category'].queryset = BudgetCategory.objects.filter(user=user)

    def clean_month(self):
        month_str = self.cleaned_data['month']
        try:
            # Convert YYYY-MM to YYYY-MM-01 for proper date storage
            date_obj = datetime.strptime(month_str, '%Y-%m')
            return date_obj.replace(day=1)
        except ValueError:
            raise forms.ValidationError('Invalid date format. Please use the month picker.') 