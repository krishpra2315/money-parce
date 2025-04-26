from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SavingsContribution
from .forms import SavingsContributionForm
from transactions.models import Transaction

# Create your views here.

@login_required
def contribution_list(request):
    contributions = SavingsContribution.objects.filter(user=request.user)
    total_percentage = sum(contribution.percentage for contribution in contributions)
    return render(request, 'savings/contribution_list.html', {
        'contributions': contributions,
        'total_percentage': total_percentage
    })

@login_required
def contribution_income_sources(request, contribution_id):
    contribution = get_object_or_404(SavingsContribution, id=contribution_id, user=request.user)
    # Get all income transactions that have contributed to this savings
    income_transactions = Transaction.objects.filter(
        user=request.user,
        transaction_type='income'
    ).order_by('-date')
    
    # Calculate savings amount for each transaction
    transactions_with_savings = []
    for transaction in income_transactions:
        savings_amount = (transaction.amount * contribution.percentage) / 100
        transactions_with_savings.append({
            'transaction': transaction,
            'savings_amount': savings_amount
        })
    
    return render(request, 'savings/contribution_income_sources.html', {
        'contribution': contribution,
        'transactions_with_savings': transactions_with_savings
    })

@login_required
def create_contribution(request):
    if request.method == 'POST':
        form = SavingsContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.user = request.user
            
            # Check if total percentage would exceed 100%
            existing_total = sum(
                c.percentage for c in 
                SavingsContribution.objects.filter(user=request.user)
            )
            if existing_total + contribution.percentage > 100:
                messages.error(request, 'Total contribution percentage cannot exceed 100%')
                return render(request, 'savings/create_contribution.html', {'form': form})
            
            contribution.save()
            messages.success(request, 'Savings contribution created successfully!')
            return redirect('savings:contribution_list')
    else:
        form = SavingsContributionForm()
    return render(request, 'savings/create_contribution.html', {'form': form})

@login_required
def delete_contribution(request, contribution_id):
    contribution = get_object_or_404(SavingsContribution, id=contribution_id, user=request.user)
    if request.method == 'POST':
        contribution.delete()
        messages.success(request, 'Savings contribution deleted successfully!')
        return redirect('savings:contribution_list')
    return render(request, 'savings/delete_contribution.html', {'contribution': contribution})
