from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Goal
from .forms import GoalForm, ContributionForm

# Create your views here.

@login_required
def goal_list(request):
    goals = Goal.objects.filter(user=request.user)
    return render(request, 'goals/goal_list.html', {'goals': goals})

@login_required
def create_goal(request):
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, 'Goal created successfully!')
            return redirect('goals:goal_list')
    else:
        form = GoalForm()
    return render(request, 'goals/create_goal.html', {'form': form})

@login_required
def contribute_to_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            contribution = form.cleaned_data['amount']
            goal.current_amount += contribution
            goal.save()
            messages.success(request, f'Successfully contributed ${contribution} to {goal.name}')
            return redirect('goals:goal_list')
    else:
        form = ContributionForm()
    return render(request, 'goals/contribute.html', {'form': form, 'goal': goal})

@login_required
def delete_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Goal deleted successfully!')
        return redirect('goals:goal_list')
    return render(request, 'goals/delete_goal.html', {'goal': goal})
