"""
ZohoManager: Uses raw HTTP requests for Zoho CRM integration.
NOTE: The official Zoho Python SDK was not working reliably in this environment, so the requests library is used instead for direct API calls.
This version includes automatic access token refresh using the refresh_token.

If needed, can run `python lib/generate_zoho_tokens.py` to generate a new access token.
"""
import os
import logging
from typing import Dict, Any
import requests
from lib.env_vars import ZOHO_CONFIG_PATH
import json
import time

logger = logging.getLogger(__name__)

class ZohoManager:
    """
    Manages Zoho CRM integration for lead creation using raw HTTP requests.
    Automatically refreshes the access token using the refresh_token.
    """
    def __init__(self):
        self.config = self._load_config()
        self.access_token = self.config.get("access_token") or os.environ.get("ZOHO_ACCESS_TOKEN")
        self.refresh_token = self.config.get("refresh_token")
        self.client_id = self.config.get("client_id")
        self.client_secret = self.config.get("client_secret")
        self.api_base_url = self.config.get("apiBaseUrl", "https://www.zohoapis.com")
        self.api_version = self.config.get("apiVersion", "v8")
        self.token_expiry = 0  # Unix timestamp
        if not self.refresh_token or not self.client_id or not self.client_secret:
            raise ValueError("Zoho refresh_token, client_id, and client_secret must be present in config for token refresh.")
        if not self.access_token or self._token_expired():
            self._refresh_access_token()

    def _load_config(self) -> dict:
        if not ZOHO_CONFIG_PATH or not os.path.isfile(ZOHO_CONFIG_PATH):
            logger.warning(f"ZOHO_CONFIG_PATH ('{ZOHO_CONFIG_PATH}') does not exist. Proceeding with environment variables only.")
            return {}
        try:
            with open(ZOHO_CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Zoho config: {e}")
            return {}

    def _token_expired(self) -> bool:
        # Consider token expired if less than 2 minutes left
        return not self.token_expiry or time.time() > self.token_expiry - 120

    def _refresh_access_token(self):
        """
        Refresh the Zoho access token using the refresh_token.
        Updates self.access_token and self.token_expiry.
        """
        url = "https://accounts.zoho.com/oauth/v2/token"
        data = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            resp_json = response.json()
            self.access_token = resp_json["access_token"]
            expires_in = int(resp_json.get("expires_in", 3600))
            self.token_expiry = time.time() + expires_in
            logger.info("Refreshed Zoho access token.")
            # Optionally update config file with new access token
            self._update_config_access_token(self.access_token)
        except Exception as e:
            logger.error(f"Failed to refresh Zoho access token: {e}")
            raise

    def _update_config_access_token(self, access_token: str):
        # Optionally update the config file with the new access token
        if not ZOHO_CONFIG_PATH or not os.path.isfile(ZOHO_CONFIG_PATH):
            return
        try:
            with open(ZOHO_CONFIG_PATH, "r") as f:
                config = json.load(f)
            config["access_token"] = access_token
            with open(ZOHO_CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.warning(f"Could not update access token in config file: {e}")

    def create_lead(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new lead in Zoho CRM using the v8 API.
        Args:
            data: Dictionary with lead fields (expects at least first/last name, email, company)
        Returns:
            Zoho API response as a dict
        Raises:
            Exception on failure
        """
        if not self.access_token or self._token_expired():
            self._refresh_access_token()
        url = f"{self.api_base_url}/crm/{self.api_version}/Leads"
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json"
        }
        # Map input data to Zoho fields
        zoho_data = {
            "First_Name": data.get("first_name") or (data.get("name", "").split()[0] if "name" in data else None),
            "Last_Name": data.get("last_name") or (" ".join(data.get("name", "").split()[1:]) if "name" in data and len(data["name"].split()) > 1 else None),
            "Email": data.get("email"),
            "Company": data.get("company"),
            "Designation": data.get("role")
        }
        # Add any additional fields
        for k, v in data.items():
            if k not in {"first_name", "last_name", "name", "email", "company", "role"}:
                zoho_data[k] = v
        # Remove None values
        zoho_data = {k: v for k, v in zoho_data.items() if v}
        payload = {"data": [zoho_data]}
        try:
            response = requests.post(url, headers=headers, json=payload)
            logger.info(f"Zoho lead creation response: {response.status_code}")
            try:
                resp_json = response.json()
            except Exception:
                resp_json = {"raw": response.text}
            if not response.ok:
                logger.error(f"Zoho API error: {resp_json}")
                raise Exception(f"Zoho API error: {resp_json}")
            return {"status_code": response.status_code, "response": resp_json}
        except Exception as e:
            logger.error(f"Failed to create Zoho lead: {e}")
            raise

if __name__ == "__main__":
    """
    Standalone test for ZohoManager: attempts to create a sample lead in Zoho CRM.
    Requires valid Zoho refresh token, client_id, and client_secret in config.
    """
    logging.basicConfig(level=logging.INFO)
    try:
        manager = ZohoManager()
        sample_lead = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com",
            "company": "Acme Corp",
            "role": "VP of Sales"
        }
        print("Creating test lead in Zoho CRM...")
        result = manager.create_lead(sample_lead)
        print(f"Lead creation result: {result}")
    except Exception as e:
        print(f"Error during Zoho lead creation: {e}")
