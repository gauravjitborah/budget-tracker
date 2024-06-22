import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Define the scope and credentials file (downloaded from Google Cloud Console)
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('monthly-budget-tool-ed454f8c302c.json', scope)

# Authenticate using the credentials
client = gspread.authorize(creds)

# Open the Google Sheet (replace 'MySheet' with your actual Google Sheet name)
sheet = client.open('BudgetTracker').sheet1

# Example data to write (replace with your actual data)
data = [
    ["Bank", "Amount", "Vendor", "Date"],
    ["HDFC", 3000.00, "CITY CORPORATION LTD", datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
]

# Append the data to the sheet
sheet.append_rows(data)

print("Data successfully appended to Google Sheet.")