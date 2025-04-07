from django import forms
from .models import Transaction
from django.utils import timezone
from django.db.models import Max, Min

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['name', 'amount', 'category', 'date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date', 
                'value': timezone.now().strftime('%Y-%m-%d')
            }),
        }

class TransactionFilterForm(forms.Form):
    name = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by name'})
    )
    
    category = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Filter by category'})
    )
    
    max_amount = forms.DecimalField(
        required=False, 
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Max amount',
            'step': '0.01'
        })
    )
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If a user is provided, we can get distinct categories from their transactions
        if user and user.is_authenticated:
            transactions = Transaction.objects.filter(user=user)
            categories = list(transactions.values_list('category', flat=True).distinct())
            
            if categories:
                self.fields['category'] = forms.ChoiceField(
                    required=False,
                    choices=[('', 'All Categories')] + [(c, c) for c in categories],
                    widget=forms.Select(attrs={'class': 'form-control'})
                ) 