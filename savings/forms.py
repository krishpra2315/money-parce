from django import forms
from .models import SavingsContribution

class SavingsContributionForm(forms.ModelForm):
    class Meta:
        model = SavingsContribution
        fields = ['name', 'percentage']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
        }
        labels = {
            'name': 'Savings Name (e.g., 401k, 529 Plan)',
            'percentage': 'Contribution Percentage'
        } 