import re
import csv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Email Authentication Flow
def authenticate_gmail():
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', scopes=SCOPES)
    creds = flow.run_local_server(port=0)
    return creds

# Identify the emails from specific sender
def get_sender_email(message_id, service):
    message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    headers = message['payload']['headers']
    for header in headers:
        if header['name'] == 'From':
            return header['value']
    return 'Sender email not found'

# Transaction Details: Amount, Place, DateTime
def extract_transaction_details(message_body):
    pattern = r'Rs ([0-9,.]+) at ([\w\s]+) on (\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})'
    match = re.search(pattern, message_body)
    if match:
        amount = match.group(1)
        name = match.group(2)
        datetime_str = match.group(3)
        return amount, name, datetime_str
    else:
        return None, None, None

def list_messages_with_subject_and_sender(service, user_id, subject, sender):
    transactions = []
    try:
        # List messages matching the criteria
        response = service.users().messages().list(
            userId=user_id,
            q=f'subject:"{subject}" from:"{sender}" is:unread'
        ).execute()
        messages = response.get('messages', [])

        if not messages:
            print('No messages found.')
        else:
            print('Messages:')
            for message in messages:
                msg = service.users().messages().get(userId=user_id, id=message['id']).execute()
                message_body = msg['snippet']  # Assuming snippet contains the message body
                amount, name, datetime_str = extract_transaction_details(message_body)
                if amount and name and datetime_str:
                    transactions.append({
                        'Message ID': message['id'],
                        'Amount': amount,
                        'Name': name,
                        'Datetime': datetime_str
                    })
                    #print(f" - Message ID: {message['id']}")
                    print(f"   Amount: {amount}")
                    print(f"   Name: {name}")
                    print(f"   Datetime: {datetime_str}")
    except HttpError as error:
        print(f'An error occurred: {error}')

    return transactions

# Export the data to CSV file transactions.csv
def export_to_csv(transactions, output_file='transactions.csv'):
    if not transactions:
        print('No transactions to export.')
        return

    fields = ['Message ID', 'Amount', 'Name', 'Datetime']

    with open(output_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for transaction in transactions:
            writer.writerow(transaction)

    print(f'Transactions exported to {output_file} successfully.')

def main():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    # Specify the criteria
    subject = 'Alert : Update on your HDFC Bank Credit Card'
    sender = 'alerts@hdfcbank.net'

    # Call the Gmail API

    results = list_unread_messages(service, 'me')
    messages = results.get('messages', [])

    transactions = list_messages_with_subject_and_sender(service, 'me', subject, sender)

    # Export transactions to CSV file
    export_to_csv(transactions)

    '''
    if not messages:
        print('No messages found.')
    else:
        print('Messages:')
        for message in messages:
            sender_email = get_sender_email(message['id'], service)
            print(f" - Message ID: {message['id']}, Sender: {sender_email}")
    '''
if __name__ == '__main__':
    main()