import os
import openai
from django.conf import settings
from .models import Transaction # Import Transaction to access CATEGORY_CHOICES

# --- OpenAI Setup (similar to users/utils.py but scoped here) ---
# Load the API key from settings (which should load from environment variables)
openai_api_key = os.environ.get('OPENAI_API_KEY')

# Simplified Plaid category hierarchy (examples)
# See: https://plaid.com/docs/transactions/categories/#category-hierarchy
PLAID_TO_APP_CATEGORY_MAP = {
    # Food and Drink
    'FOOD_AND_DRINK': 'food',
    'Restaurants': 'food',
    'Groceries': 'food',
    # Transportation
    'TRANSPORTATION': 'transportation',
    'Gas Stations': 'transportation',
    'Public Transportation': 'transportation',
    'Ride Share': 'transportation',
    # Shopping
    'SHOPS': 'shopping',
    'Clothing and Accessories': 'shopping',
    'Department Stores': 'shopping',
    'Electronics': 'shopping',
    # Entertainment
    'ENTERTAINMENT': 'entertainment',
    'Movies and DVDs': 'entertainment',
    'Music': 'entertainment',
    'Games': 'entertainment',
    # Housing
    'RENT': 'housing',
    'MORTGAGE': 'housing',
    # Utilities
    'UTILITIES': 'utilities',
    'Internet': 'utilities',
    'Mobile Phone': 'utilities',
    # Subscriptions/Services
    'SERVICE': 'subscriptions',
    'Subscription': 'subscriptions',
    'Financial': 'other', # Often fees, map to other for now
    # Income
    'TRANSFER_IN': 'income',
    'TRANSFER_OUT': 'other', # Could be payment, keep as other
    'PAYMENT': 'other',
    'Payroll': 'income',
    'Interest Earned': 'income',
    # Healthcare
    'HEALTHCARE': 'healthcare',
    'Doctor': 'healthcare',
    'Pharmacy': 'healthcare',
    # Personal Care
    'PERSONAL_CARE': 'personal_care',
    'Gyms and Fitness Centers': 'personal_care',
    # Travel
    'TRAVEL': 'travel',
    'Airlines and Aviation Services': 'travel',
    'Hotels and Motels': 'travel',
    # Education
    'EDUCATION': 'education',
    'Tuition': 'education',
    # Gifts & Donations
    'GENERAL_SERVICES_Charities_and_Non-Profits': 'gifts_donations',
    'GENERAL_MERCHANDISE_Gift_Card': 'gifts_donations', # Assume gift purchase is a gift

}

# Get valid app category keys from the model
VALID_APP_CATEGORIES = dict(Transaction.CATEGORY_CHOICES).keys()

def map_plaid_category(plaid_categories):
    """Maps a list of Plaid categories to the app's defined categories."""
    if not plaid_categories:
        return 'other' # Default if no Plaid category

    # Plaid returns a hierarchy (e.g., ["Shops", "Clothing and Accessories"])
    # Try mapping from most specific to least specific
    for category in reversed(plaid_categories):
        if category in PLAID_TO_APP_CATEGORY_MAP:
            app_category = PLAID_TO_APP_CATEGORY_MAP[category]
            if app_category in VALID_APP_CATEGORIES:
                return app_category

    # If no direct map found, try the primary category (first in list)
    primary_category = plaid_categories[0]
    if primary_category in PLAID_TO_APP_CATEGORY_MAP:
        app_category = PLAID_TO_APP_CATEGORY_MAP[primary_category]
        if app_category in VALID_APP_CATEGORIES:
            return app_category

    # --- Fallback to OpenAI if direct mapping fails --- 
    # Uncomment and refine this section if you want AI fallback
    # print(f"No direct map for Plaid categories: {plaid_categories}. Trying OpenAI.")
    # ai_category = get_category_from_openai(plaid_categories, Transaction.CATEGORY_CHOICES)
    # if ai_category in VALID_APP_CATEGORIES:
    #     print(f"OpenAI mapped {plaid_categories} to: {ai_category}")
    #     return ai_category
    # else:
    #     print(f"OpenAI fallback failed or returned invalid category for: {plaid_categories}")

    return 'other' # Final fallback


def get_category_from_openai(plaid_categories, app_category_choices):
    """
    Uses OpenAI API to determine the best app category based on Plaid categories.
    (Requires OPENAI_API_KEY in environment)
    """
    if not openai_api_key:
        print("OpenAI API key not configured. Cannot use AI for category mapping.")
        return 'other'

    try:
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Format the available choices for the prompt
        available_choices_str = ", ".join([f"'{key}' ({label})" for key, label in app_category_choices if key != 'income']) # Exclude income for spending typically
        
        prompt = (
            f"Given the Plaid transaction categories: {plaid_categories}, "
            f"which of the following application categories best fits? "
            f"Available categories are: {available_choices_str}. "
            f"Respond with ONLY the category key (e.g., 'food', 'shopping', 'other'). "
            f"If it represents income or a deposit, respond with 'income'. If unsure, respond with 'other'."
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Use a cheaper/faster model for this
            messages=[
                {"role": "system", "content": "You are an assistant that maps transaction categories."}, 
                {"role": "user", "content": prompt}
            ],
            temperature=0.2, # Low temperature for consistency
            max_tokens=15,
            n=1,
            stop=None,
        )

        if response.choices:
            ai_choice = response.choices[0].message.content.strip().lower().replace("'", "")
            # Basic validation: Ensure the returned key is one of the expected ones
            if ai_choice in dict(app_category_choices).keys():
                return ai_choice
            else:
                print(f"OpenAI returned unexpected category key: '{ai_choice}' for Plaid categories: {plaid_categories}")
                return 'other' # Fallback if AI gives garbage
        else:
            print("OpenAI API response for category mapping did not contain choices.")
            return 'other'

    except Exception as e:
        print(f"An error occurred during OpenAI category mapping: {e}")
        return 'other' # Fallback on any API error 