from .models import MonthlyBudget
from reminders.models import BillReminder
from django.utils import timezone
from django.urls import reverse_lazy

def budget_alerts(request):
    alerts_context = {
        'budget_alerts': [],
        'upcoming_reminders_alerts': []
    }
    if request.user.is_authenticated:
        budget_alerts_list = MonthlyBudget.get_current_alerts(request.user)
        alerts_context['budget_alerts'] = budget_alerts_list

        try:
            today = timezone.now().date()
            three_days_later = today + timezone.timedelta(days=3)

            upcoming_reminders = BillReminder.objects.filter(
                user=request.user,
                is_paid=False,
                due_date__gte=today,
                due_date__lte=three_days_later
            ).order_by('due_date')

            reminder_alerts_list = []
            for reminder in upcoming_reminders:
                reminder_alerts_list.append({
                    'message': f"Reminder: '{reminder.title}' due {reminder.due_date.strftime('%b %d')}",
                    'level': 'info',
                    'link': reverse_lazy('bill_reminders')
                })
            alerts_context['upcoming_reminders_alerts'] = reminder_alerts_list
        except Exception as e:
            print(f"Error fetching reminder alerts for user {request.user.email}: {e}")
            # Keep the list empty on error

    return alerts_context 