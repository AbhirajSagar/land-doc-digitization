import json
import os
from typing import Optional
from google.oauth2 import service_account
import google.auth
from dotenv import load_dotenv

load_dotenv()

_cached_credentials = None

def get_credentials():
    """Retrieve Google Cloud credentials from environment variable or application defaults."""
    global _cached_credentials
    if _cached_credentials is not None:
        return _cached_credentials

    creds_raw = os.getenv("GOOGLE_CLOUD_CREDENTIALS")
    if creds_raw:
        try:
            # Check if it is a JSON string
            if creds_raw.strip().startswith("{"):
                credentials_json = json.loads(creds_raw)
                _cached_credentials = service_account.Credentials.from_service_account_info(
                    credentials_json,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
            # Check if it is a file path
            elif os.path.isfile(creds_raw):
                _cached_credentials = service_account.Credentials.from_service_account_file(
                    creds_raw,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
        except Exception as e:
            print(f"Warning: Failed to load service account credentials from GOOGLE_CLOUD_CREDENTIALS: {e}")

    if _cached_credentials is None:
        try:
            _cached_credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        except Exception as e:
            print(f"Warning: Could not load default Google credentials: {e}")

    return _cached_credentials