import pandas as pd
from datetime import datetime

# Function to process timestamp column or add a new one
def process_timestamps(input_file, output_file, timestamp_column, date_time_format="%Y-%m-%d %H:%M:%S"):
    # Read the input Excel file
    df = pd.read_excel(input_file)
    
    # Check if the timestamp column exists
    if timestamp_column in df.columns:
        # Convert existing timestamps to the specified format
        df[timestamp_column] = pd.to_datetime(df[timestamp_column], errors='coerce').dt.strftime(date_time_format)
    else:
        # Add a new timestamp column with the current date and time
        current_time = datetime.now().strftime(date_time_format)
        df[timestamp_column] = current_time
        print(f"The column '{timestamp_column}' was not found. A new column with the current timestamp was added.")
    
    # Save the updated Excel file
    df.to_excel(output_file, index=False)
    print(f"Updated Excel file saved as {output_file}")

# Example usage
input_file = "Whatsapp_Final_Data_News - Dainik Bhaskar Hindi - India, Rajasthan, Madhya Pradesh, MP, CG, UP, Bihar, Delhi_2024-11-23_FINAL.xlsx"  # Replace with your input Excel file
output_file = "output.xlsx"  # Replace with your desired output file name
timestamp_column = "timestamp"  # Replace with your desired timestamp column name
date_time_format = "%Y-%m-%d %H:%M:%S"  # Replace with your desired date-time format

process_timestamps(input_file, output_file, timestamp_column, date_time_format)
