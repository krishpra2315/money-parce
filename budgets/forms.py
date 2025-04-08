from django import forms
from .models import BudgetCategory, MonthlyBudget
from django.contrib.auth.models import User
from transactions.models import Transaction

class BudgetCategoryForm(forms.ModelForm):
    class Meta:
        model = BudgetCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MonthlyBudgetForm(forms.ModelForm):
    class Meta:
        model = MonthlyBudget
        fields = ['category', 'amount', 'month']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'month': forms.DateInput(attrs={'class': 'form-control', 'type': 'month'}),
        }

    def __init__(self, user, *args, **kwargs):
        super(MonthlyBudgetForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = BudgetCategory.objects.filter(user=user) 