import pandas as pd

df_a = pd.read_excel("crossed_resistance_output.xlsx")   # small
df_b = pd.read_excel("23_JAN_2026.xlsx")                  # big

df_b = df_b.rename(columns={"Stock": "ticker"})

# Clean tickers
for df in [df_a, df_b]:
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()

# A -> B merge (resistance lookup)
merged = df_a.merge(df_b[["ticker","Color"]], on="ticker", how="left", indicator=True)
not_in_23jan = merged[merged["_merge"] == "left_only"]

# B -> A merge (master lookup)
reverse = df_b.merge(df_a[["ticker"]], on="ticker", how="left", indicator=True)
not_in_resistance = reverse[reverse["_merge"] == "left_only"]

# Save
with pd.ExcelWriter("final_merge.xlsx") as w:
    merged.to_excel(w, sheet_name="Resistance_With_Color", index=False)
    not_in_23jan.to_excel(w, sheet_name="Missing_In_23Jan", index=False)
    not_in_resistance.to_excel(w, sheet_name="Missing_In_Resistance", index=False)

print("Done. 3 sheets created.")
