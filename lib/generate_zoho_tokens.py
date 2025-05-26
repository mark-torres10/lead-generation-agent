"""Generates t"""

import requests
from urllib.parse import urlencode
from pathlib import Path

from lib.env_vars import (
    ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REDIRECT_URI, ZOHO_AUTH_CODE
)


# NOTE: doesn't work, need to go to the UI and generate a code manually, and
# it only does it for minutes at a time.
def construct_zoho_auth_url():
    """Generate Zoho auth code for the leads AI agent system."""
    
    # Debug: Print the redirect URI to verify it matches Zoho app configuration
    print(f"Using redirect URI: {ZOHO_REDIRECT_URI}")
    print("Ensure this EXACTLY matches the redirect URI configured in your Zoho Developer Console")
    
    url = "https://accounts.zoho.com/oauth/v2/auth"
    params = {
        "response_type": "code",
        "client_id": ZOHO_CLIENT_ID,
        "redirect_uri": ZOHO_REDIRECT_URI,
        "scope": "ZohoCRM.modules.ALL,ZohoCRM.settings.ALL",
        "access_type": "offline"
    }
    
    # Use urlencode to properly encode URL parameters
    auth_url = f"{url}?{urlencode(params)}"
    
    return auth_url

def generate_zoho_tokens():
    """Generate Zoho tokens for the leads AI agent system."""
    url = "https://accounts.zoho.com/oauth/v2/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "redirect_uri": ZOHO_REDIRECT_URI,
        "code": ZOHO_AUTH_CODE
    }
    response = requests.post(url, data=data)
    return response.json()

def refresh_zoho_tokens(refresh_token):
    """Refresh Zoho tokens for the leads AI agent system."""
    url = "https://accounts.zoho.com/oauth/v2/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "refresh_token": refresh_token
    }
    response = requests.post(url, data=data)
    return response.json()

if __name__ == "__main__":
    # if needed, generate a new auth code
    # print(construct_zoho_auth_url())

    # else, read from env and save access token to .env
    tokens = generate_zoho_tokens()
    print(tokens)
    
    # Save the access token to .env file
    if 'access_token' in tokens:
        env_path = Path(__file__).parent.parent / ".env"
        
        # Read existing .env content
        env_lines = []
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add ZOHO_ACCESS_TOKEN
        token_line = f"ZOHO_ACCESS_TOKEN={tokens['access_token']}\n"
        updated = False
        
        for i, line in enumerate(env_lines):
            if line.startswith('ZOHO_ACCESS_TOKEN='):
                env_lines[i] = token_line
                updated = True
                break
        
        if not updated:
            env_lines.append(token_line)
        
        # Write back to .env file
        with open(env_path, 'w') as f:
            f.writelines(env_lines)
        
        print(f"Saved ZOHO_ACCESS_TOKEN to {env_path}")
