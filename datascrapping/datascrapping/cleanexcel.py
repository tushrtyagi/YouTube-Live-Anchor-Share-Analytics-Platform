import pandas as pd
import re
from datetime import datetime

# Load the original file
file_name = 'Whatsapp_Final_Data_News - Dainik Bhaskar Hindi - India, Rajasthan, Madhya Pradesh, MP, CG, UP, Bihar, Delhi_2024-11-23'  # Replace with your file path
data = pd.read_excel(f"{file_name}.xlsx")

# Function to extract time and date from the 'timestamp' column
def extract_time_and_date(timestamp):
    # Regular expression to capture time and date
    time_date_pattern = r'\[(.*?), (\d{1,2}/\d{1,2}/\d{4})\]'
    match = re.search(time_date_pattern, timestamp)
    if match:
        time_str, date_str = match.groups()
        
        # Convert time to 24-hour format
        try:
            time_obj = datetime.strptime(time_str, '%I:%M %p')
            time_24 = time_obj.strftime('%H:%M')
        except ValueError:
            time_24 = time_str  # Keep original if already in 24-hour format
        
        return time_24, date_str
    else:
        return 'Time Not Found', 'Date Not Found'

# Apply the extraction function
data['time'], data['date'] = zip(*data['timestamp'].apply(extract_time_and_date))

# Function to extract links from the 'content' column
def extract_links(text):
    return ', '.join(re.findall(r'(https?://\S+)', str(text)))

data['links'] = data['content'].apply(extract_links)

# Reorder columns
columns_order = ['channel', 'date', 'time', 'content', 'links', 'reaction_count']
data = data[columns_order]

# Save the updated data to a new Excel file
output_file_path = f'{file_name}_FINAL.xlsx'
data.to_excel(output_file_path, index=False)

print(f"File saved successfully as {output_file_path}")