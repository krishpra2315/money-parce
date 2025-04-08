from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from .models import BillReminder
from .forms import BillReminderForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from django.shortcuts import render
from .models import BillReminder
from django.contrib.auth.decorators import login_required

@login_required
def bill_reminders(request):
    # Get the reminders for the logged-in user
    reminders = BillReminder.objects.filter(user=request.user).order_by('due_date')
    return render(request, 'reminders/bill_reminders.html', {'reminders': reminders})

class BillReminderCreateView(LoginRequiredMixin, CreateView):
    model = BillReminder
    form_class = BillReminderForm
    template_name = 'reminders/reminder_form.html'
    success_url = reverse_lazy('bill_reminders')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class BillReminderUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BillReminder
    form_class = BillReminderForm
    template_name = 'reminders/reminder_form.html'
    success_url = reverse_lazy('bill_reminders')

    def test_func(self):
        reminder = self.get_object()
        return reminder.user == self.request.user

class BillReminderDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = BillReminder
    template_name = 'reminders/reminder_confirm_delete.html'
    success_url = reverse_lazy('bill_reminders')

    def test_func(self):
        reminder = self.get_object()
        return reminder.user == self.request.user
