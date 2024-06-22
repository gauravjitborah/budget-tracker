import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Read the CSV file into a DataFrame
df = pd.read_csv('transactions.csv')

# Convert the date_time column to datetime type
df['date_time'] = pd.to_datetime(df['date_time'], format='%d-%m-%Y %H:%M:%S', errors='coerce')

# Drop rows with invalid date_time
df = df.dropna(subset=['date_time'])

# Set the date_time column as the index
df.set_index('date_time', inplace=True)

# Resample the data by day and sum the amount for each bank
daily_expenses = df.resample('D').sum()
daily_expenses = daily_expenses.reset_index()

# Filter for specific banks
banks_of_interest = ['HDFC', 'AU Bank', 'Kotak', 'HSBC']
filtered_expenses = daily_expenses[daily_expenses['bank'].isin(banks_of_interest)]

# Plot the data
plt.figure(figsize=(14, 7))
sns.lineplot(data=filtered_expenses, x='date_time', y='amount', hue='bank', marker='o')

plt.title('Daily Credit Card Expenses by Bank')
plt.xlabel('Date')
plt.ylabel('Amount')
plt.xticks(rotation=45)
plt.legend(title='Bank')
plt.tight_layout()
plt.show()