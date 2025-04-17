from django import forms
from .models import Scholarship, CollegeDebt

class ScholarshipForm(forms.ModelForm):
    class Meta:
        model = Scholarship
        fields = ['name', 'amount']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
        }

class CollegeDebtForm(forms.ModelForm):
    class Meta:
        model = CollegeDebt
        fields = ['total_amount']
        widgets = {
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        }
        labels = {
            'total_amount': 'Total College Debt Amount ($)'
        } 