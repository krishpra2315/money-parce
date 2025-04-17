from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from .models import Transaction
from .forms import TransactionForm, TransactionFilterForm
import datetime

@login_required
def transaction_list(request):
    """View to handle both adding new transactions and displaying the list of transactions."""
    
    # Initialize transactions queryset with the current user's transactions
    transactions = Transaction.objects.filter(user=request.user)
    
    # Process the filter form if it's a GET request with parameters
    filter_form = TransactionFilterForm(data=request.GET or None)
    if request.GET and filter_form.is_valid():
        # Apply filters based on form data
        name_filter = filter_form.cleaned_data.get('name')
        category_filter = filter_form.cleaned_data.get('category')
        max_amount_filter = filter_form.cleaned_data.get('max_amount')
        month_filter = filter_form.cleaned_data.get('month')
        year_filter = filter_form.cleaned_data.get('year')
        
        # Filter by name (partial match)
        if name_filter:
            transactions = transactions.filter(name__icontains=name_filter)
        
        # Filter by category
        if category_filter:
            transactions = transactions.filter(category=category_filter)
        
        # Filter by max amount
        if max_amount_filter is not None:
            transactions = transactions.filter(amount__lte=max_amount_filter)
            
        # Filter by month and year
        if month_filter and year_filter:
            transactions = transactions.filter(date__month=month_filter, date__year=year_filter)
        # Filter by month only (across all years)
        elif month_filter:
            transactions = transactions.filter(date__month=month_filter)
        # Filter by year only (across all months)
        elif year_filter:
            transactions = transactions.filter(date__year=year_filter)
    
    # Handle form submission for new transaction
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            # Create transaction but don't save to DB yet
            transaction = form.save(commit=False)
            # Add the current user
            transaction.user = request.user
            # Now save to DB
            transaction.save()
            messages.success(request, "Transaction added successfully!")
            return redirect('transactions:transaction_list')
    else:
        form = TransactionForm()
    
    return render(request, 'transactions/transaction_list.html', {
        'form': form,
        'filter_form': filter_form,
        'transactions': transactions,
    })

@login_required
def delete_transaction(request, transaction_id):
    """View to delete a transaction."""
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, "Transaction deleted successfully!")
    
    # Preserve filter parameters when redirecting back to the list view
    if request.GET:
        redirect_url = f"{request.path.replace(f'delete/{transaction_id}/', '')}?{request.GET.urlencode()}"
        return HttpResponseRedirect(redirect_url)
    
    return redirect('transactions:transaction_list')
