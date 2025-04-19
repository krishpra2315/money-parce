import os
import openai
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
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

@receiver(post_save, sender=Transaction)
def handle_transaction_save(sender, instance, created, **kwargs):
    """
    After a transaction is saved, check corresponding budget thresholds
    and trigger OpenAI suggestion if needed.
    """
    transaction = instance
    logger.info(f"Signal received for Transaction ID: {transaction.id}, Category: {transaction.category}, Date: {transaction.date}, User: {transaction.user.username}")
    budget_month_start = date(transaction.date.year, transaction.date.month, 1)

    try:
        # Find the relevant monthly budget
        logger.debug(f"Attempting to find budget for User: {transaction.user.id}, Category Code: {transaction.category}, Month Start: {budget_month_start}")
        monthly_budget = MonthlyBudget.objects.get(
            user=transaction.user,
            category__name=transaction.category, # Match based on category name/code
            month=budget_month_start
        )
        logger.debug(f"Found MonthlyBudget ID: {monthly_budget.id}")

        # Check and reset flag if spending dropped below threshold before this transaction
        monthly_budget.check_and_reset_suggestion_flag()

        # Recalculate progress *after* this transaction might have affected it
        current_progress = monthly_budget.get_progress_percentage()
        logger.info(f"Budget ID: {monthly_budget.id} - Current Progress: {current_progress:.2f}%, Suggestion Generated Flag: {monthly_budget.suggestion_generated}")

        # Check conditions: Over threshold and suggestion not yet generated
        if current_progress >= 80 and not monthly_budget.suggestion_generated:
            logger.info(f"Threshold crossed for Budget ID: {monthly_budget.id} ({monthly_budget.category.get_name_display()}). Generating AI suggestion...")
            generate_ai_suggestion(monthly_budget)
        else:
            logger.info(f"Conditions not met for generating suggestion for Budget ID: {monthly_budget.id}.")

    except MonthlyBudget.DoesNotExist:
        logger.warning(f"No MonthlyBudget found for User: {transaction.user.username}, Category Code: {transaction.category}, Month: {budget_month_start}")
    except Exception as e:
        logger.error(f"Error in handle_transaction_save signal for Transaction ID {transaction.id}: {e}", exc_info=True)


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

        transaction_list_str = "\n".join([
            f"- {t.date}: {t.name} (${t.amount})" for t in recent_transactions
        ])

        # 2. Construct the prompt
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