import pandas as pd
import json

# Path to your Excel file
INPUT_FILE = "nifty_indices_with_constituents.xlsx"
OUTPUT_FILE = "nifty_indices_list_json.txt"

# Read Excel file
df = pd.read_excel(INPUT_FILE)

# Prepare the list of dictionaries
result_list = []

for _, row in df.iterrows():
    if row['Status'] != 'SUCCESS':
        continue  # Skip rows where data fetch was not successful

    # Safely handle NaN values by converting to string
    constituents_str = str(row['Constituents']) if pd.notna(row['Constituents']) else "nan"
    link_str = str(row['SourceURL']) if pd.notna(row['SourceURL']) else "nan"

    ticker_data = {
        row['YFTicker']: {  # Use YFTicker as key
            "Name": str(row['IndexName']),
            "ticker": str(row['YFTicker']),
            "constituents": [x.strip() for x in constituents_str.split(",")],
            "link": link_str
        }
    }

    result_list.append(ticker_data)

# Write to .txt file as JSON list
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(result_list, f, indent=4)

print(f"Data successfully written to {OUTPUT_FILE}")
