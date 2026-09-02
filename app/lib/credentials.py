import json
import os
from google.oauth2 import service_account

from dotenv import load_dotenv
load_dotenv()

credentials_json = json.loads(os.getenv("GOOGLE_CLOUD_CREDENTIALS"))
credentials = service_account.Credentials.from_service_account_info(
    credentials_json,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

def get_credentials():
    return credentials