from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Path to the service account key file
SERVICE_ACCOUNT_FILE = 'monthly-budget-tool-ed454f8c302c.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
DELEGATED_EMAIL = 'gauravjitborah@gmail.com'  # Email of the user to impersonate

# Create credentials using the service account key file
credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Delegate the credentials to the user
delegated_credentials = credentials.with_subject(DELEGATED_EMAIL)

# Build the Gmail API client
service = build('gmail', 'v1', credentials=delegated_credentials)

# Example: List the user's Gmail messages
results = service.users().messages().list(userId='me').execute()
messages = results.get('messages', [])

for message in messages:
    print(message)