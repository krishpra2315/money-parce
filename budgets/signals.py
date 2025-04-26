import os
import openai
from decimal import Decimal
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.db.models import Sum
from transactions.models import Transaction
from .models import MonthlyBudget
from datetime import date
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

# --- OpenAI Configuration ---
# Ensure you have OPENAI_API_KEY in your .env file
# and load_dotenv() is called (usually in settings.py or manage.py)
try:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        print("Warning: OPENAI_API_KEY not found in environment variables.")
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
# --------------------------

# --- Helper Function to Update Budget Spent Amount --- 
def update_budget_spent_amount(user, category_code, budget_month):
    """Recalculates and updates the spent amount for a specific budget."""
    try:
        monthly_budget = MonthlyBudget.objects.get(
            user=user,
            category__name=category_code,
            month=budget_month
        )
        logger.debug(f"Found budget ID {monthly_budget.id} to update spent amount for {category_code} / {budget_month}.")

        # Calculate total spent: Sum positive amounts where type is 'expense'
        total_spent = Transaction.objects.filter(
            user=user,
            category=category_code,
            date__year=budget_month.year,
            date__month=budget_month.month,
            transaction_type='expense' # Filter by transaction type
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Amount is already positive, no need for abs()
        new_spent_amount = total_spent 

        if monthly_budget.spent_amount != new_spent_amount:
            logger.info(f"Updating spent amount for Budget ID {monthly_budget.id} from {monthly_budget.spent_amount} to {new_spent_amount}")
            monthly_budget.spent_amount = new_spent_amount
            # Save without triggering signals again, only update spent_amount
            monthly_budget.save(update_fields=['spent_amount'])
            return monthly_budget # Return the updated budget
        else:
            logger.debug(f"Spent amount for Budget ID {monthly_budget.id} is already up-to-date.")
            return monthly_budget # Return the budget even if no change

    except MonthlyBudget.DoesNotExist:
        logger.warning(f"Cannot update spent amount: No MonthlyBudget found for User: {user.username}, Category Code: {category_code}, Month: {budget_month}")
        return None
    except Exception as e:
        logger.error(f"Error updating spent amount for User {user.username}, Category {category_code}, Month {budget_month}: {e}", exc_info=True)
        return None


@receiver(post_save, sender=Transaction)
def handle_transaction_save(sender, instance, created, **kwargs):
    """
    After a transaction is saved, update the corresponding budget's spent amount
    and then check thresholds for AI suggestions.
    """
    transaction = instance
    # Ignore income transactions for budget expense tracking
    if transaction.transaction_type == 'income': # Check type instead of amount sign
        logger.info(f"Skipping budget update for income Transaction ID: {transaction.id}")
        return

    logger.info(f"Signal received for Expense Transaction ID: {transaction.id}, Category: {transaction.category}, Date: {transaction.date}, User: {transaction.user.username}")
    budget_month_start = date(transaction.date.year, transaction.date.month, 1)

    # --- Update Spent Amount FIRST ---
    monthly_budget = update_budget_spent_amount(
        transaction.user, 
        transaction.category, 
        budget_month_start
    )
    # --- End Update Spent Amount ---

    # Continue with AI suggestion logic only if budget was found/updated
    if monthly_budget:
        try:
            # Check and reset flag if spending dropped below threshold before this transaction
            # (spent amount updated above, so check_and_reset now uses the latest value)
            monthly_budget.check_and_reset_suggestion_flag()

            # Recalculate progress with the potentially updated spent_amount
            current_progress = monthly_budget.get_progress_percentage()
            logger.info(f"Budget ID: {monthly_budget.id} - Current Progress: {current_progress:.2f}%, Suggestion Generated Flag: {monthly_budget.suggestion_generated}")

            # Check conditions: Over threshold and suggestion not yet generated
            if current_progress >= 80 and not monthly_budget.suggestion_generated:
                logger.info(f"Threshold crossed for Budget ID: {monthly_budget.id} ({monthly_budget.category.get_name_display()}). Generating AI suggestion...")
                generate_ai_suggestion(monthly_budget)
            else:
                logger.info(f"Conditions not met for generating suggestion for Budget ID: {monthly_budget.id}.")

        except Exception as e:
            logger.error(f"Error in handle_transaction_save signal (AI part) for Transaction ID {transaction.id}, Budget ID {monthly_budget.id}: {e}", exc_info=True)
    else:
         logger.warning(f"Skipping AI check because budget could not be found or updated for Transaction ID {transaction.id}.")


# --- New Signal Handler for Deletion ---
@receiver(post_delete, sender=Transaction)
def handle_transaction_delete(sender, instance, **kwargs):
    """
    After a transaction is deleted, update the corresponding budget's spent amount.
    """
    transaction = instance
    # Ignore income transactions for budget expense tracking
    if transaction.transaction_type == 'income': # Check type instead of amount sign
        logger.info(f"Skipping budget update for deleted income Transaction ID: {transaction.id}")
        return
    
    logger.info(f"Delete signal received for Expense Transaction ID: {transaction.id}, Category: {transaction.category}, Date: {transaction.date}, User: {transaction.user.username}")
    budget_month_start = date(transaction.date.year, transaction.date.month, 1)

    # Update the budget's spent amount
    update_budget_spent_amount(
        transaction.user,
        transaction.category,
        budget_month_start
    )
    logger.info(f"Budget spent amount update triggered after deletion of Transaction ID: {transaction.id}")


def generate_ai_suggestion(monthly_budget):
    """
    Fetches recent transactions, calls OpenAI API, and saves the suggestion.
    """
    if not openai.api_key:
        logger.warning("Skipping AI suggestion: OpenAI API key not configured.")
        return
    logger.debug(f"Starting AI suggestion generation for Budget ID: {monthly_budget.id}")

    try:
        # 1. Get recent transactions for the prompt context
        recent_transactions = Transaction.objects.filter(
            user=monthly_budget.user,
            category=monthly_budget.category.name,
            date__year=monthly_budget.month.year,
            date__month=monthly_budget.month.month
        ).order_by('-date')[:10] # Get last 10 transactions in this category/month

        if not recent_transactions:
            logger.warning("Skipping AI suggestion: No recent transactions found for context.")
            return

        # Update transaction list string if needed (amount is now always positive)
        transaction_list_str = "\n".join([
            f"- {t.date}: {t.name} (${t.amount})" for t in recent_transactions
        ]) # Amount is already positive here

        # 2. Construct the prompt (Ensure it makes sense with positive amounts)
        prompt = f"""
        You are a helpful financial assistant. A user has spent {monthly_budget.get_progress_percentage():.1f}% of their budget for the '{monthly_budget.category.get_name_display()}' category this month.
        Their recent spending in this category includes:
        {transaction_list_str}

        Based on this spending, please provide 2-3 concise and actionable suggestions for cheaper alternatives or ways to save money in the '{monthly_budget.category.get_name_display()}' category for the rest of the month. Be specific if possible, referencing the types of items purchased. Avoid generic advice like "spend less".
        """

        # 3. Call OpenAI API (using ChatCompletion)
        logger.info("Calling OpenAI API...")
        client = openai.OpenAI() # Use the client instance
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a helpful financial assistant providing concise saving tips."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150, # Adjust as needed
            temperature=0.7   # just creativity
        )

        suggestion = response.choices[0].message.content.strip()
        logger.info(f"AI Suggestion received: {suggestion}")

        # 4. Save the suggestion and update the flag
        monthly_budget.ai_suggestion = suggestion
        monthly_budget.suggestion_generated = True
        monthly_budget.save(update_fields=['ai_suggestion', 'suggestion_generated'])
        logger.info("AI Suggestion saved.")

    except openai.APIError as e:
      # Handle API error here, e.g. retry or log
      logger.error(f"OpenAI API returned an API Error: {e}", exc_info=True)
    except openai.AuthenticationError as e:
      logger.error(f"OpenAI Authentication Error: {e}", exc_info=True)
    except openai.RateLimitError as e:
      logger.error(f"OpenAI Rate Limit Exceeded: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error during AI suggestion generation for Budget ID {monthly_budget.id}: {e}", exc_info=True) 