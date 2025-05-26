import os.path
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class GoogleAPICore:
    """
    Base class for Google API integrations. Handles OAuth2 credential loading, token refresh,
    and service building for Google APIs.
    """
    def __init__(
        self,
        api_name: str,
        api_version: str,
        scopes: list[str],
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None,
    ):
        self.api_name = api_name
        self.api_version = api_version
        self.scopes = scopes
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.credentials_path = credentials_path or os.path.join(self.current_dir, "credentials.json")
        self.token_path = token_path or os.path.join(self.current_dir, "token.json")
        self.service = self._get_service()

    def _get_service(self):
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.scopes)
                creds = flow.run_local_server(port=0)
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
        return build(self.api_name, self.api_version, credentials=creds) 