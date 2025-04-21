from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.views import (
    LoginView, 
    LogoutView, 
    PasswordResetView, 
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from .forms import UserRegistrationForm, UserLoginForm, UserPasswordResetForm, UserSetPasswordForm, ProfileUpdateForm
from django.utils import timezone
from .utils import get_daily_financial_tip

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

class CustomLoginView(LoginView):
    form_class = UserLoginForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('home')

    def form_valid(self, form):
        """Check and generate daily tip after successful login."""
        login(self.request, form.get_user())
        user = form.get_user()
        today = timezone.now().date()

        if user.last_tip_date is None or user.last_tip_date < today:
            try:
                prompt = "Provide a general, concise personal finance tip suitable for a wide audience. "
                if user.age:
                    prompt += f"Keep in mind the user is {user.age} years old, but don't make the tip overly specific to this age. "
                else:
                    prompt += "The user has not provided their age. "
                prompt += "Focus on actionable advice or positive financial habits."

                tip = get_daily_financial_tip(prompt) 

                if tip:
                    user.daily_tip = tip
                    user.last_tip_date = today
                    user.save(update_fields=['daily_tip', 'last_tip_date'])
                else:
                    print(f"Daily tip generation skipped or failed for user {user.email}")

            except Exception as e:
                print(f"Error during tip processing for user {user.email}: {e}") 

        return redirect(self.get_success_url())

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
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "There was an error updating your profile. Please check the form.")
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'users/profile.html', {'form': form})
