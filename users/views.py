from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.views import (
    LogoutView, 
    PasswordResetView, 
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from .forms import UserRegistrationForm, UserPasswordResetForm, UserSetPasswordForm, ProfileUpdateForm
from django.utils import timezone
from .utils import get_daily_financial_tip
from django_otp.plugins.otp_totp.models import TOTPDevice
# Import models for previews
from transactions.models import Transaction
from goals.models import Goal
from budgets.models import MonthlyBudget
from reminders.models import BillReminder
import json # Add json import
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseServerError # Add JsonResponse etc.
from django.contrib.auth.decorators import login_required # Add login_required
from django.views.decorators.http import require_POST # Add require_POST
from django.conf import settings # Import settings

from . import plaid_utils # Import the new plaid utils

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect('home')
        messages.error(request, "Registration failed. Please check the information provided.")
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

class CustomLogoutView(LogoutView):
    template_name = 'users/logout.html'
    http_method_names = ['get', 'post']
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, "You have been successfully logged out.")
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
        return render(request, self.template_name)

class CustomPasswordResetView(PasswordResetView):
    form_class = UserPasswordResetForm
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = UserSetPasswordForm
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'

@login_required
def profile(request):
    user = request.user
    two_factor_enabled = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
    plaid_linked = user.plaid_access_token is not None and user.plaid_item_id is not None

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            # Re-check states after save, though plaid_linked shouldn't change here
            two_factor_enabled = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
            plaid_linked = user.plaid_access_token is not None and user.plaid_item_id is not None
            # Redirect to profile GET request to avoid form resubmission issues
            return redirect('profile') 
        else:
            messages.error(request, "There was an error updating your profile. Please check the form.")
    else:
        form = ProfileUpdateForm(instance=user)
    
    context = {
        'form': form,
        'two_factor_enabled': two_factor_enabled,
        'plaid_linked': plaid_linked, # Pass plaid connection status
        'plaid_institution_name': user.plaid_institution_name, # Pass institution name if linked
        'PLAID_CLIENT_ID': settings.PLAID_CLIENT_ID, # Pass client ID for Plaid Link initialization
    }
    return render(request, 'users/profile.html', context)

def home_view(request):
    """
    View for the home page, handling both authenticated and
    unauthenticated users.
    """
    context = {
        'daily_tip': None,
        # Add previews for authenticated users
        'recent_transactions': None,
        'active_goals': None,
        'recent_budgets': None,
        'upcoming_reminders': None,
        # Add other default context variables if needed
    }

    if request.user.is_authenticated:
        user = request.user
        today = timezone.now().date()
        daily_tip = user.daily_tip # Get the potentially existing tip

        # Fetch preview data
        try:
            context['recent_transactions'] = Transaction.objects.filter(user=user).order_by('-date')[:3]
            context['active_goals'] = Goal.objects.filter(user=user).order_by('-updated_at')[:3] # Order by most recently updated instead of non-existent status
            context['recent_budgets'] = MonthlyBudget.objects.filter(user=user).order_by('-month')[:3] # Corrected model name and ordering field
            context['upcoming_reminders'] = BillReminder.objects.filter(user=user, due_date__gte=today, is_paid=False).order_by('due_date')[:3] # Corrected model name and added is_paid=False
        except Exception as e:
            # Log error if fetching preview data fails
            print(f"Error fetching preview data for user {user.email}: {e}")
            # Optionally set previews to empty lists or handle differently
            context['recent_transactions'] = []
            context['active_goals'] = []
            context['recent_budgets'] = []
            context['upcoming_reminders'] = []

        # Check if a new tip should be generated
        if user.last_tip_date is None or user.last_tip_date < today:
            try:
                prompt = "Provide a general, concise personal finance tip suitable for a wide audience. "
                if user.age:
                    prompt += f"Keep in mind the user is {user.age} years old, but don't make the tip overly specific to this age. "
                else:
                    prompt += "The user has not provided their age. "
                prompt += "Focus on actionable advice or positive financial habits."

                new_tip = get_daily_financial_tip(prompt)

                if new_tip:
                    user.daily_tip = new_tip
                    user.last_tip_date = today
                    user.save(update_fields=['daily_tip', 'last_tip_date'])
                    daily_tip = new_tip # Update the tip for the context
                else:
                    # Tip generation failed or was skipped, keep the old tip (or None)
                    print(f"Daily tip generation skipped or failed for user {user.email}")

            except Exception as e:
                # Log the error but don't prevent the home page from loading
                print(f"Error during tip processing for user {user.email}: {e}")
                # Keep the potentially existing daily_tip

        # Update context for authenticated users
        context['daily_tip'] = daily_tip
        # Add any other context needed only for logged-in users
        # context['budget_alerts'] = get_budget_alerts(user) # Example if using a context processor already

    # For unauthenticated users, context remains with default values (e.g., daily_tip=None)

    return render(request, 'home.html', context)


# --- Plaid Integration Views ---

@login_required
def create_link_token_view(request):
    """View to generate a Plaid Link token."""
    link_token = plaid_utils.create_link_token(request.user.id)
    if link_token:
        return JsonResponse({'link_token': link_token})
    else:
        # Use request._request for messages with JsonResponse if needed, but better to return error in JSON
        # messages.error(request._request, "Could not initialize Plaid Link. Please try again later.") 
        return JsonResponse({'error': 'Could not create link token'}, status=500)

@login_required
@require_POST
# Consider CSRF protection if this endpoint is called directly from a form,
# but usually it's called via AJAX/fetch from Plaid Link's JS callback.
# If using fetch from the same origin, CSRF should be handled automatically by Django.
# from django.views.decorators.csrf import csrf_exempt
# @csrf_exempt
def exchange_public_token_view(request):
    """View to exchange a Plaid public token for an access token."""
    try:
        data = json.loads(request.body)
        public_token = data.get('public_token')
        metadata = data.get('metadata', {})
        institution = metadata.get('institution', {})
        institution_name = institution.get('name')
        institution_id = institution.get('institution_id') # Optionally store this too

        if not public_token:
            return HttpResponseBadRequest(json.dumps({'error': "Missing public_token"}), content_type="application/json")

        access_token, item_id = plaid_utils.exchange_public_token(public_token)

        if access_token and item_id:
            user = request.user
            user.plaid_access_token = access_token
            user.plaid_item_id = item_id
            user.plaid_institution_name = institution_name
            # user.plaid_institution_id = institution_id # Save if you added the field
            user.save(update_fields=['plaid_access_token', 'plaid_item_id', 'plaid_institution_name'])
            # Use request._request for messages with JsonResponse is tricky, prefer JSON response
            # messages.success(request._request, f"Successfully linked your account with {institution_name or 'your bank'}.") 
            return JsonResponse({'status': 'success', 'item_id': item_id, 'institution_name': institution_name})
        else:
            # messages.error(request._request, "Could not exchange public token. Plaid connection failed.")
            return JsonResponse({'error': 'Could not exchange public token'}, status=500)
    except json.JSONDecodeError:
        return HttpResponseBadRequest(json.dumps({'error': "Invalid JSON data"}), content_type="application/json")
    except Exception as e:
        print(f"Error exchanging public token: {e}") # Log the error
        # messages.error(request._request, "An unexpected error occurred during Plaid connection.")
        return JsonResponse({'error': "Server error during token exchange"}, status=500)


@login_required
def manage_plaid_connection_view(request):
    """View to display Plaid connection status and management options."""
    user = request.user
    context = {
        'plaid_linked': user.plaid_access_token is not None and user.plaid_item_id is not None,
        'plaid_institution_name': user.plaid_institution_name,
    }
    return render(request, 'users/manage_plaid.html', context)

@login_required
@require_POST
def remove_plaid_connection_view(request):
    """View to remove the Plaid connection for the user."""
    user = request.user
    if user.plaid_access_token:
        removed = plaid_utils.remove_item(user.plaid_access_token)
        if removed:
            institution_name = user.plaid_institution_name or "your bank"
            user.plaid_access_token = None
            user.plaid_item_id = None
            user.plaid_institution_name = None
            user.save(update_fields=['plaid_access_token', 'plaid_item_id', 'plaid_institution_name'])
            messages.success(request, f"Successfully disconnected your account with {institution_name}.")
        else:
            messages.error(request, "Could not disconnect your bank account. Please try again.")
    else:
        messages.warning(request, "No bank account is currently linked.")

    return redirect('manage_plaid_connection') # Redirect back to the management page
