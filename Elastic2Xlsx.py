import json
import pandas as pd

# Load your JSON file (or paste JSON into a variable)
with open("crossed_resistance.json", "r") as f:
    data = json.load(f)

rows = []

for item in data:
    src = item["_source"]
    ticker = src["ticker"]

    # crossed_resistance is a list
    for cr in src.get("crossed_resistance", []):
        rows.append({
            "ticker": ticker,
            "resistance": cr.get("resistance_level"),
            "support": cr.get("support_level")
        })

# Convert to DataFrame
df = pd.DataFrame(rows)

# Save to Excel
df.to_excel("crossed_resistance_output.xlsx", index=False)

print("Excel file created: crossed_resistance_output.xlsx")
