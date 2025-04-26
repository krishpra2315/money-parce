from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from .models import Transaction
from .forms import TransactionForm, TransactionFilterForm
from .category_mapper import map_plaid_category
from users.plaid_utils import get_transactions_sync
from django.db import transaction as db_transaction
import datetime

@login_required
def transaction_list(request):
    """View to handle both adding new transactions and displaying the list of transactions."""
    
    # Initialize transactions queryset with the current user's transactions
    transactions = Transaction.objects.filter(user=request.user)
    
    # Process the filter form if it's a GET request with parameters
    filter_form = TransactionFilterForm(request.GET or None) # Instantiate with GET data (or None)
    
    # Apply filters ONLY if the form is valid 
    if filter_form.is_valid():
        # Access cleaned_data *after* validation
        cleaned_data = filter_form.cleaned_data # Store cleaned_data for easier access
        print("Filter form is valid. Cleaned data:", cleaned_data) # Debug log
        name_filter = cleaned_data.get('name')
        category_filter = cleaned_data.get('category')
        max_amount_filter = cleaned_data.get('max_amount')
        month_filter = cleaned_data.get('month')
        year_filter = cleaned_data.get('year')
        
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
    else:
        # Add this else block to see validation errors
        if request.GET:
            print("Filter form is NOT valid. Errors:", filter_form.errors.as_json()) # Debug log errors
    
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

# --- Helper Function for Processing Sync Data ---
def _process_plaid_transactions(user, added_tx, modified_tx, removed_tx_ids):
    """Helper to process synced transaction data atomically."""
    added_count = 0
    updated_count = 0
    removed_count = 0

    with db_transaction.atomic(): # Ensure all or nothing updates
        # Remove transactions
        if removed_tx_ids:
            num_deleted, _ = Transaction.objects.filter(
                user=user,
                plaid_transaction_id__in=[r['transaction_id'] for r in removed_tx_ids]
            ).delete()
            removed_count = num_deleted

        # Process added and modified transactions
        transactions_to_process = added_tx + modified_tx
        plaid_ids_to_update = {t['transaction_id'] for t in transactions_to_process}
        
        # Fetch existing transactions matching these Plaid IDs for efficient updates
        existing_transactions = Transaction.objects.filter(
            user=user,
            plaid_transaction_id__in=plaid_ids_to_update
        ).in_bulk(field_name='plaid_transaction_id')

        transactions_to_create = []
        transactions_to_update = []

        for tx_data in transactions_to_process:
            plaid_id = tx_data['transaction_id']
            app_category = map_plaid_category(tx_data.get('category'))
            
            # Determine transaction type and store positive amount
            plaid_amount = tx_data['amount'] 
            # Plaid debit (expense) is positive, credit (income) is negative.
            
            if plaid_amount < 0: # Negative amount from Plaid means INCOME
                transaction_type = 'income'
                amount = abs(plaid_amount) # Store positive value
                final_category = 'income' # Force category to income
            else: # Positive or zero amount from Plaid means EXPENSE
                transaction_type = 'expense'
                amount = plaid_amount # Store positive value (or zero)
                final_category = app_category # Use the mapped category

            defaults = {
                'name': tx_data.get('merchant_name') or tx_data.get('name', 'N/A'),
                'amount': amount, # Store the positive amount
                'transaction_type': transaction_type, # Store the type
                'category': final_category,
                'date': tx_data['date'],
                'plaid_account_id': tx_data['account_id'],
                'pending': tx_data.get('pending', False),
                'user': user, # Ensure user is set
            }

            existing_tx = existing_transactions.get(plaid_id)
            if existing_tx:
                # Update existing transaction
                update_needed = False
                for field, value in defaults.items():
                    if getattr(existing_tx, field) != value:
                        setattr(existing_tx, field, value)
                        update_needed = True
                if update_needed:
                    transactions_to_update.append(existing_tx)
                    updated_count += 1
            else:
                # Prepare to create new transaction
                transactions_to_create.append(
                    Transaction(plaid_transaction_id=plaid_id, **defaults)
                )
                added_count += 1

        # Bulk create new transactions
        if transactions_to_create:
            Transaction.objects.bulk_create(transactions_to_create)
            
        # Bulk update existing transactions
        if transactions_to_update:
            update_fields = ['name', 'amount', 'transaction_type', 'category', 'date', 'plaid_account_id', 'pending', 'user']
            Transaction.objects.bulk_update(transactions_to_update, update_fields)

    return added_count, updated_count, removed_count


# --- New Sync View ---
@login_required
def sync_plaid_transactions(request):
    """Initiates a transaction sync with Plaid for the logged-in user."""
    user = request.user
    
    if not user.plaid_access_token:
        messages.error(request, "No Plaid account linked. Please link an account first.")
        # Redirect to profile or manage page based on your flow
        return redirect('profile') 
        
    access_token = user.plaid_access_token
    cursor = user.plaid_sync_cursor

    sync_result = get_transactions_sync(access_token, cursor)

    if sync_result is None:
        messages.error(request, "Could not fetch transactions from Plaid. Please try again later or re-link your account if the issue persists.")
    else:
        added_tx, modified_tx, removed_tx_ids, next_cursor = sync_result
        
        try:
            added_count, updated_count, removed_count = _process_plaid_transactions(
                user, added_tx, modified_tx, removed_tx_ids
            )
            
            # Update the user's sync cursor
            user.plaid_sync_cursor = next_cursor
            user.save(update_fields=['plaid_sync_cursor'])
            
            messages.success(request, f"Sync complete! Added: {added_count}, Updated: {updated_count}, Removed: {removed_count} transactions.")

        except Exception as e:
            # Log the exception
            print(f"Error processing Plaid transactions for user {user.email}: {e}")
            messages.error(request, "An error occurred while saving synced transactions.")

    # Redirect back to the transaction list or another appropriate page
    return redirect('transactions:transaction_list')
