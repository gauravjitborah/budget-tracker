import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

import os, pickle
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

TOKEN_FILE = 'token.pickle'

# Define the scope and credentials file (downloaded from Google Cloud Console)
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
#creds = ServiceAccountCredentials.from_json_keyfile_name('GoogleSheetAccess.json', scope)

# Email Authentication Flow
def authenticate_gmail():
    creds = None
    
    # Check if the token file exists
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, prompt the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh the credentials if they have expired
            creds.refresh(Request())
        else:
            # Initiate the authentication flow
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

creds = authenticate_gmail()

# Authenticate using the credentials
client = gspread.authorize(creds)

# Open the Google Sheet (replace 'MySheet' with your actual Google Sheet name)
sheet = client.open('Budget Tracker').sheet1

# Example data to write (replace with your actual data)
data = [
    ["Bank", "Amount", "Vendor", "Date"],
    ["HDFC", 3000.00, "CITY CORPORATION LTD", datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
]

# Append the data to the creds_type
sheet.append_rows(data)

print("Data successfully appended to Google Sheet.")