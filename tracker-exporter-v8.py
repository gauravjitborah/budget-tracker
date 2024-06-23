'''
This script has 3 parts to it:
1) Email Authentication Flow
2) Check Emails for potential match (on a daily basis)
3) Export the data to Google Sheet - BudgetTracker
'''
import re
import os
import pickle
import csv
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials
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
OUTPUT_FILE = 'transactions-3.csv'
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
    
    # Get today's date in YYYY/MM/DD format (eg: '2024/06/21')
    #today = datetime.today().date().strftime('%Y/%m/%d')
    today = '2024/06/21'

    
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
        'HDFC': r'Thank you for using your HDFC Bank Credit Card ending \d+ for Rs ([\d,.]+) at ([\w\s]+) on (\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})',
        'HSBC': r'Credit card no ending with \d+,has been used for INR ([\d,.]+) for payment to ([\w\s]+) on (\d{2} \w{3} \d{4} at \d{2}:\d{2})',
        'Kotak': r'A Transaction of INR ([\d,.]+) has been done on your Kotak Bank Credit Card No\.xx\d+ at ([\w-]+) on (\d{2}-\w{3}-\d{4})',
        'AU': r'INR ([\d,.]+) were spent on your AU Bank Credit Card xx\d+ at ([\w\s]+) on (\d{2}-\d{2}-\d{4} at \d{2}:\d{2}:\d{2} \w{2})',
        'Axis': r'Thank you for using your Card no. XX\d+ for INR ([\d,.]+) at ([\w\s]+) on (\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})',
        'ICICI': r'Your ICICI Bank Credit Card XX\d+ has been used for a transaction of INR ([\d,.]+) on (\w{3} \d{2}, \d{4} at \d{2}:\d{2}:\d{2}).*Info: ([\w\s]+)\.',
        'IDFC': r'INR ([\d,.]+) spent on your IDFC FIRST Bank Credit Card ending XX\d+ at ([\w\s]+) on (\d{2}-\w{3}-\d{4} at \d{2}:\d{2} \w{2})'
    }

    match = re.search(patterns[bank_name], snippet)
    if match:
        # Attempt to extract amount, location, and date_time
        try:
            # Format datetime to bring it all to the same format
            if bank_name == 'HDFC':
                amount, location, date_time = match.groups()
                date_time = datetime.strptime(date_time, '%d-%m-%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S') #21-06-2024 18:18:15
            elif bank_name == 'HSBC':
                amount, location, date_time = match.groups()
                date_time = datetime.strptime(date_time, '%d %b %Y at %H:%M').strftime('%Y-%m-%d %H:%M:%S') #18 Jun 2024 at 22:58
            elif bank_name == 'Kotak':
                amount, location, date_time = match.groups()
                date_time = datetime.strptime(date_time, '%d-%b-%Y').strftime('%Y-%m-%d %H:%M:%S') #21-Jun-2024
            if bank_name == 'AU':
                amount, location, date_time = match.groups()
                date_time = datetime.strptime(date_time, '%d-%m-%Y at %I:%M:%S %p').strftime('%Y-%m-%d %H:%M:%S') #21-06-2024 at 03:12:09
            elif bank_name == 'Axis':
                amount, location, date_time = match.groups()
                date_time = datetime.strptime(date_time, '%d-%m-%y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S') #30-04-24 23:16:46
            elif bank_name == 'ICICI':
                amount, date_time, location = match.groups()
                date_time = datetime.strptime(date_time, '%b %d, %Y at %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S') #May 08, 2024 at 12:51:23
            if bank_name == 'IDFC':
                amount, location, date_time = match.groups()
                date_time = datetime.strptime(date_time, '%d-%b-%Y at %I:%M %p').strftime('%Y-%m-%d %H:%M:%S') #11-APR-2024 at 05:38 PM

        except ValueError:
            print(match.groups(),snippet)
            print(f"Error parsing email for {bank_name}: Unexpected format.")
            return None
        
        return {
            'Date': date_time,
            'Bank': bank_name,
            'Amount': amount.replace(',', ''),  # Remove commas from amount for consistent formatting
            'Vendor': location
        }
    else:
        #print(f"No match found for {bank_name}.")
        return None

def check_emails(service):
    # List of Bank email IDs and Subject
    queries = [
        {'Bank': 'HDFC', 'subject': 'Alert : Update on your HDFC Bank Credit Card', 'sender': 'alerts@hdfcbank.net'},
        {'Bank': 'HSBC', 'subject': 'You have used your HSBC Credit Card ending with', 'sender': 'hsbc@mail.hsbc.co.in'},
        {'Bank': 'Kotak', 'subject': 'Kotak Bank Credit Card Transaction Alert', 'sender': 'creditcardalerts@kotak.com'},
        {'Bank': 'AU', 'subject': 'AU Bank Credit Card Transaction Alert', 'sender': 'creditcard.alerts@aubank.in'},
        {'Bank': 'Axis', 'subject': 'Transaction alert on Axis Bank Credit Card no.', 'sender': 'alerts@axisbank.com'},
        {'Bank': 'ICICI', 'subject': 'Transaction alert for your ICICI Bank Credit Card', 'sender': 'credit_cards@icicibank.com'},
        {'Bank': 'IDFC', 'subject': 'Debit Alert: Your IDFC FIRST Bank Credit Card', 'sender': 'noreply@idfcfirstbank.com'}
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
    
    # Sort results by datetime ('Date' field)
    results.sort(key=lambda x: datetime.strptime(x['Date'], '%Y-%m-%d %H:%M:%S'))

    return results

# Define the ID and range of your Google Sheet
SPREADSHEET_ID = '12jOZDJiJgaf-IIqFCrGLZ7j9o1kEez3wRkhISRusYeU'
RANGE_NAME = 'transactions'

def get_last_row():
    # Load credentials from a service account
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    
    # Build the service
    service = build('sheets', 'v4', credentials=creds)
    
    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
        return None
    else:
        last_row = len(values)
        return values[last_row - 1]

# Export the data to Google Sheet - BudgetTracker
def upload_to_gsheet(transactions,last_row):
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

        last_entry = datetime.strptime(last_row[0], '%Y-%m-%d %H:%M:%S')
        current_entry = datetime.strptime(transaction['Date'], '%Y-%m-%d %H:%M:%S')

        # Compare last transaction to only add newer transactions
        if last_entry >= current_entry:
            continue
        else:
            sheet.append_row([transaction['Date'], transaction['Bank'], float(transaction['Amount']), transaction['Vendor']])
    
    print("Data successfully appended to Google Sheet.")

def main():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    results=check_emails(service)
    last_row=get_last_row()
    upload_to_gsheet(results,last_row)

if __name__ == '__main__':
    main()