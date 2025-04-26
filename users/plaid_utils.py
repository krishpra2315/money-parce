import os
from django.conf import settings
import plaid
from plaid.api import plaid_api
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.item_remove_request import ItemRemoveRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
import datetime

# Determine Plaid environment based on settings
if settings.PLAID_ENV == 'sandbox':
    host = plaid.Environment.Sandbox
elif settings.PLAID_ENV == 'development':
    host = plaid.Environment.Development
else:
    host = plaid.Environment.Production

# Configure Plaid client
configuration = plaid.Configuration(
    host=host,
    api_key={
        'clientId': settings.PLAID_CLIENT_ID,
        'secret': settings.PLAID_SECRET,
    }
)
api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# Convert string settings to Plaid enums
PLAID_PRODUCTS_ENUM = [Products(product) for product in settings.PLAID_PRODUCTS]
PLAID_COUNTRY_CODES_ENUM = [CountryCode(code) for code in settings.PLAID_COUNTRY_CODES]

def create_link_token(user_id):
    """Creates a Plaid Link token for a given user."""
    try:
        request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(
                client_user_id=str(user_id) # Must be a string
            ),
            client_name="MoneyParce",
            products=PLAID_PRODUCTS_ENUM,
            country_codes=PLAID_COUNTRY_CODES_ENUM,
            language='en',
            # webhook='YOUR_WEBHOOK_URL' # Optional: Add if using webhooks
            # redirect_uri='YOUR_REDIRECT_URI' # Optional: Add if using OAuth redirect flow
        )
        response = client.link_token_create(request)
        return response['link_token']
    except plaid.ApiException as e:
        # Handle API errors (log them, return None or raise custom exception)
        print(f"Error creating Plaid link token: {e}")
        return None

def exchange_public_token(public_token):
    """Exchanges a public token for an access token and item ID."""
    try:
        request = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        response = client.item_public_token_exchange(request)
        return response['access_token'], response['item_id']
    except plaid.ApiException as e:
        print(f"Error exchanging Plaid public token: {e}")
        return None, None

def remove_item(access_token):
    """Removes a Plaid Item (disconnects the account)."""
    try:
        request = ItemRemoveRequest(access_token=access_token)
        response = client.item_remove(request)
        # response contains {'removed': True, 'request_id': '...'} on success
        return response['removed']
    except plaid.ApiException as e:
        print(f"Error removing Plaid item: {e}")
        return False

def get_transactions_sync(access_token, cursor=None):
    """Fetches transactions using Plaid's sync endpoint.

    Args:
        access_token: The Plaid access token for the item.
        cursor: The cursor from the previous sync response (optional).

    Returns:
        A tuple containing: (added_tx, modified_tx, removed_tx_ids, next_cursor)
        or None if an error occurs.
    """
    added = []
    modified = []
    removed = []
    has_more = True
    
    while has_more:
        try:
            # Conditionally create the request based on cursor presence
            if cursor:
                request = TransactionsSyncRequest(access_token=access_token, cursor=cursor)
            else:
                # For the initial sync, don't include the cursor parameter in the request object
                request = TransactionsSyncRequest(access_token=access_token)
            
            response = client.transactions_sync(request)
            
            # Add new transactions to the list
            added.extend(response['added'])
            modified.extend(response['modified'])
            removed.extend(response['removed']) # These are transaction IDs
            
            has_more = response['has_more']
            # Update the cursor to the next cursor provided by the response
            cursor = response['next_cursor']
            
        except plaid.ApiException as e:
            print(f"Error during Plaid transactions sync: {e}")
            # Depending on the error, you might want to handle item errors
            # (e.g., ITEM_LOGIN_REQUIRED) by prompting the user to re-authenticate.
            return None # Return None or raise an exception on error

    return added, modified, removed, cursor

# Add more Plaid API call functions here as needed (e.g., fetch transactions)
# def get_transactions(access_token, start_date, end_date): ...
# def get_accounts(access_token): ... 