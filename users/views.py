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

def profile(request):
    user = request.user
    two_factor_enabled = TOTPDevice.objects.filter(user=user, confirmed=True).exists()

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            two_factor_enabled = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
            return redirect('profile')
        else:
            messages.error(request, "There was an error updating your profile. Please check the form.")
    else:
        form = ProfileUpdateForm(instance=user)
    
    context = {
        'form': form,
        'two_factor_enabled': two_factor_enabled
    }
    return render(request, 'users/profile.html', context)

def home_view(request):
    """
    View for the home page, handling both authenticated and
    unauthenticated users.
    """
    context = {
        'daily_tip': None,
        # Add other default context variables if needed
    }

    if request.user.is_authenticated:
        user = request.user
        today = timezone.now().date()
        daily_tip = user.daily_tip # Get the potentially existing tip

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
