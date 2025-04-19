from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import BudgetCategory, MonthlyBudget
from .forms import BudgetCategoryForm, MonthlyBudgetForm
from django.db.models import Sum
from datetime import datetime

@login_required
def budget_dashboard(request):
    categories = BudgetCategory.objects.filter(user=request.user)
    current_month = datetime.now().replace(day=1)
    budgets = MonthlyBudget.objects.filter(
        user=request.user,
        month__year=current_month.year,
        month__month=current_month.month
    )
    
    total_budget = budgets.aggregate(total=Sum('amount'))['total'] or 0
    total_spent = sum(budget.get_spent_amount() for budget in budgets)
    
    # Calculate total progress percentage
    total_progress = (total_spent / total_budget * 100) if total_budget > 0 else 0
    
    context = {
        'categories': categories,
        'budgets': budgets,
        'total_budget': total_budget,
        'total_spent': total_spent,
        'total_progress': total_progress,
        'current_month': current_month.strftime('%B %Y')
    }
    return render(request, 'budgets/dashboard.html', context)

@login_required
def create_category(request):
    if request.method == 'POST':
        form = BudgetCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Budget category created successfully!')
            return redirect('budgets:budget_dashboard')
    else:
        form = BudgetCategoryForm()
    
    return render(request, 'budgets/category_form.html', {'form': form})

@login_required
def create_budget(request):
    if request.method == 'POST':
        form = MonthlyBudgetForm(request.user, request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            messages.success(request, 'Monthly budget created successfully!')
            return redirect('budgets:budget_dashboard')
    else:
        form = MonthlyBudgetForm(request.user)
    
    return render(request, 'budgets/budget_form.html', {'form': form})

@login_required
def edit_budget(request, budget_id):
    budget = get_object_or_404(MonthlyBudget, id=budget_id, user=request.user)
    if request.method == 'POST':
        form = MonthlyBudgetForm(request.user, request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget updated successfully!')
            return redirect('budgets:budget_dashboard')
    else:
        form = MonthlyBudgetForm(request.user, instance=budget)
    
    return render(request, 'budgets/budget_form.html', {'form': form, 'budget': budget})

@login_required
def delete_budget(request, budget_id):
    budget = get_object_or_404(MonthlyBudget, id=budget_id, user=request.user)
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget deleted successfully!')
        return redirect('budgets:budget_dashboard')
    return render(request, 'budgets/confirm_delete.html', {'budget': budget}) 