import openai
from django.conf import settings
import os

# --- New file: users/utils.py ---

# Load the API key from settings (which should load from environment variables)
openai.api_key = os.environ.get('OPENAI_API_KEY')
# Or, if using the newer client:
# client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


def get_daily_financial_tip(prompt: str) -> str | None:
    """
    Generates a financial tip using the OpenAI API based on the provided prompt.

    Args:
        prompt: The prompt to send to the OpenAI API.

    Returns:
        The generated tip as a string, or None if an error occurs or the API key is missing.
    """
    if not openai.api_key:
        print("OpenAI API key not found in settings. Skipping tip generation.")
        return None

    try:
        # --- Using the newer OpenAI client (recommended) ---
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant providing concise financial tips."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, # Adjust for creativity vs. predictability
            max_tokens=60,   # Limit the length of the tip
            n=1,
            stop=None,       # Add stop sequences if needed
        )
        
        if response.choices:
            tip = response.choices[0].message.content.strip()
            return tip
        else:
            print("OpenAI API response did not contain choices.")
            return None

    except openai.AuthenticationError as e:
        print(f"OpenAI API Authentication Error: {e}. Check your API key.")
        return None
    except openai.RateLimitError as e:
        print(f"OpenAI API Rate Limit Exceeded: {e}. Please check your plan and usage.")
        return None
    except openai.APIConnectionError as e:
        print(f"OpenAI API Connection Error: {e}. Check network connectivity.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching the financial tip: {e}")
        return None

# --- End of file: users/utils.py --- 