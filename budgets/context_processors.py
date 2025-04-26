from .models import MonthlyBudget
from reminders.models import BillReminder
from django.utils import timezone
from django.urls import reverse_lazy

def budget_alerts(request):
    alerts_context = {
        'budget_alerts': [],
        'upcoming_reminders_alerts': [],
        'total_alerts_count': 0  # Initialize count
    }
    if request.user.is_authenticated:
        budget_alerts_list = MonthlyBudget.get_current_alerts(request.user)
        alerts_context['budget_alerts'] = budget_alerts_list

        reminder_alerts_list = []  # Initialize reminder list
        try:
            today = timezone.now().date()
            three_days_later = today + timezone.timedelta(days=3)

            upcoming_reminders = BillReminder.objects.filter(
                user=request.user,
                is_paid=False,
                due_date__gte=today,
                due_date__lte=three_days_later
            ).order_by('due_date')

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

        # Calculate total count after fetching both lists
        alerts_context['total_alerts_count'] = len(budget_alerts_list) + len(reminder_alerts_list)

    return alerts_context 