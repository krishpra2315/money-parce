from django import forms
from .models import Transaction
from django.utils import timezone
from django.db.models import Max, Min
import datetime

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['name', 'amount', 'category', 'date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
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
    
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'All Categories')] + Transaction.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    max_amount = forms.DecimalField(
        required=False, 
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Max amount',
            'step': '0.01'
        })
    )
    
    MONTH_CHOICES = [
        ('', 'All Months'),
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ]
    
    month = forms.ChoiceField(
        required=False,
        choices=MONTH_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Year',
            'min': '2000',
            'max': datetime.date.today().year
        })
    )
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize year with current year if not provided
        if not self.is_bound or not self.cleaned_data.get('year'):
            self.fields['year'].initial = datetime.date.today().year
        # No need for dynamic category loading anymore as we have fixed choices 