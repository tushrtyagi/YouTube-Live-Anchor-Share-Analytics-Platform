import pandas as pd

# Load both CSV files
csv1 = pd.read_csv("./vod_data.csv")
csv2 = pd.read_csv("./vod_data_indiatv.csv")

# Combine them (stacking rows)
combined_csv = pd.concat([csv1, csv2], ignore_index=True)

# Save the merged file
combined_csv.to_csv("combined.csv", index=False)

print("CSV files merged row-wise successfully!")
