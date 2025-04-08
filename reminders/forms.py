from django import forms
from .models import BillReminder

class BillReminderForm(forms.ModelForm):
    class Meta:
        model = BillReminder
        fields = ['title', 'amount', 'due_date', 'is_paid', 'notes']
