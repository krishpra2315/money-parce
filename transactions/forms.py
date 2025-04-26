from django import forms
from .models import Transaction
from django.utils import timezone
from django.db.models import Max, Min
import datetime

class TransactionForm(forms.ModelForm):
    # Define transaction_type field - it's needed for processing but might be hidden later
    transaction_type = forms.ChoiceField(
        choices=Transaction.TRANSACTION_TYPE_CHOICES, 
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}), 
        initial='expense',
        required=False # Make it not required initially, clean() will set it
    )

    class Meta:
        model = Transaction
        # Add 'transaction_type' to fields for processing
        fields = ['name', 'amount', 'category', 'date', 'transaction_type'] 
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}), # Ensure positive amount
            'category': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date', 
                'value': timezone.now().strftime('%Y-%m-%d')
            }),
            # We keep the field definition above, but can potentially hide widget in template if needed
        }

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')

        if category == 'income':
            cleaned_data['transaction_type'] = 'income'
        else:
            # Default to expense for all other categories
            cleaned_data['transaction_type'] = 'expense'
            
        # If category itself is missing, form validation would likely have failed already
        # but we ensure transaction_type is always set.
        if 'transaction_type' not in cleaned_data:
             cleaned_data['transaction_type'] = 'expense' # Fallback default

        return cleaned_data

    # Optional: Add clean_amount if needed to ensure positive values
    # def clean_amount(self):
    #     amount = self.cleaned_data.get('amount')
    #     if amount is not None and amount <= 0:
    #         raise forms.ValidationError("Amount must be positive.")
    #     return amount

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
    
    # Temporarily comment out __init__ to isolate the issue
    # def __init__(self, user=None, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # Check if data was provided and if 'year' is not in it
    #     if not self.is_bound or 'year' not in self.data or not self.data['year']:
    #         self.fields['year'].initial = datetime.date.today().year
    #     # No need for dynamic category loading anymore as we have fixed choices 