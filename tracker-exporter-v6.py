'''
This script has 3 parts to it:
1) Email Authentication Flow
2) Check Emails for potential match (on a daily basis)
3) Export the data to Google Sheet - BudgetTracker
'''
import re
import os
import pickle
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Imports for GSheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Define the contant variables
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/gmail.readonly']
TOKEN_FILE = 'token.pickle'
OUTPUT_FILE = 'transactions-2.csv'
CREDENTIALS = 'credentials.json'
SERVICE_ACCOUNT='monthly-budget-tool-ed454f8c302c.json'

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
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def search_emails(service, user_id, query):
    
    # Get today's date in YYYY/MM/DD format
    #today = '2024/06/21'
    today = datetime.today().date().strftime('%Y/%m/%d')

    
    # Append the received date filter to the query
    query += f" after:{today}"
    
    results = service.users().messages().list(userId=user_id, q=query).execute()
    messages = results.get('messages', [])
    return messages

def get_message_details(service, user_id, msg_id):
    message = service.users().messages().get(userId=user_id, id=msg_id, format='full').execute()
    snippet = message['snippet']
    return snippet

def parse_email_content(bank_name, snippet):
    patterns = {
        'HDFC': r'Thank you for using your HDFC Bank Credit Card ending 9080 for Rs ([\d,.]+) at ([\w\s]+) on (\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})',
        'HSBC': r'Credit card no ending with 9866,has been used for INR ([\d,.]+) for payment to ([\w\s]+) on (\d{2} \w{3} \d{4} at \d{2}:\d{2})',
        'Kotak': r'A Transaction of INR ([\d,.]+) has been done on your Kotak Bank Credit Card No\.xx5557 at ([\w-]+) on (\d{2}-\w{3}-\d{4})',
        'AU Bank': r'INR ([\d,.]+) were spent on your AU Bank Credit Card xx5665 at ([\w]+) on (\d{2}-\d{2}-\d{4} at \d{2}:\d{2}:\d{2} \w{2})'
    }
    
    match = re.search(patterns[bank_name], snippet)
    if match:
        amount, location, date_time = match.groups()
        return {
            'Bank': bank_name,
            'Amount': amount,
            'Vendor': location,
            'Date': date_time
        }
    return None

def check_emails(service):
    # List of Bank email IDs and Subject
    queries = [
        {'Bank': 'HDFC', 'subject': 'Alert : Update on your HDFC Bank Credit Card', 'sender': 'alerts@hdfcbank.net'},
        {'Bank': 'HSBC', 'subject': 'You have used your HSBC Credit Card ending with 9866 for a purchase transaction', 'sender': 'hsbc@mail.hsbc.co.in'},
        {'Bank': 'Kotak', 'subject': 'Kotak Bank Credit Card Transaction Alert', 'sender': 'creditcardalerts@kotak.com'},
        {'Bank': 'AU Bank', 'subject': 'AU Bank Credit Card Transaction Alert', 'sender': 'creditcard.alerts@aubank.in'}
    ]

    results = []
    for query in queries:
        search_query = f"from:{query['sender']} subject:{query['subject']}"
        messages = search_emails(service, 'me', search_query)
        
        if not messages:
            print(f"No emails found for: {query['sender']} with subject: {query['subject']}")
        else:
            for msg in messages:
                msg_id = msg['id']
                snippet = get_message_details(service, 'me', msg_id)
                parsed_data = parse_email_content(query['Bank'], snippet)
                if parsed_data:
                    results.append(parsed_data)
    return results

# Export the data to Google Sheet - BudgetTracker
def upload_to_gsheet(transactions):
    if not transactions:
        print('No transactions to export.')
        return

    # Define the scope and credentials file (downloaded from Google Cloud Console)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT, SCOPES)

    # Authenticate using the credentials
    client = gspread.authorize(creds)

    # Open the Google Sheet (replace 'MySheet' with your actual Google Sheet name)
    sheet = client.open('BudgetTracker').sheet1

    for transaction in transactions:
        #print(transaction)
        sheet.append_row([transaction['Bank'], float(transaction['Amount']), transaction['Vendor'], transaction['Date']])
    
    print("Data successfully appended to Google Sheet.")



def main():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    results=check_emails(service)
    upload_to_gsheet(results)

if __name__ == '__main__':
    main()