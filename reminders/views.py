from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .models import BillReminder
from django.contrib.auth.decorators import login_required

@login_required
def bill_reminders(request):
    user = request.user
    reminders = BillReminder.objects.filter(user=user).order_by('due_date')
    return render(request, 'reminders/bill_reminders.html', {'reminders': reminders})
