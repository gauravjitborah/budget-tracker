from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Define the ID and range of your Google Sheet
SPREADSHEET_ID = '12jOZDJiJgaf-IIqFCrGLZ7j9o1kEez3wRkhISRusYeU'
RANGE_NAME = 'transactions'  # Specify the sheet name or range

def get_last_row(service, spreadsheet_id, range_name):
    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                range=range_name).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
        return None
    else:
        last_row = len(values)
        return values[last_row - 1]

def main():
    # Load credentials from a service account
    creds = Credentials.from_service_account_file('monthly-budget-tool-ed454f8c302c.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])

    # Build the service
    service = build('sheets', 'v4', credentials=creds)

    # Get the last row entry
    last_row = get_last_row(service, SPREADSHEET_ID, RANGE_NAME)
    if last_row:
        print(f'Last row entry: {last_row}')
    else:
        print('No last row entry found.')

if __name__ == '__main__':
    main()