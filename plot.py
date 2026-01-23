import pandas as pd
import matplotlib.pyplot as plt

# ================= CONFIG =================
FILE_PATH = "icici_funds_nav.xlsx"   # Change if needed
# =========================================

# Load Excel sheets
corp = pd.read_excel(FILE_PATH, sheet_name="ICICI_Corp_Bond")
gilt = pd.read_excel(FILE_PATH, sheet_name="ICICI_Gilt")
repo = pd.read_excel(FILE_PATH, sheet_name="rbiRepoRate")

# Convert date columns
corp["date"] = pd.to_datetime(corp["date"], dayfirst=True)
gilt["date"] = pd.to_datetime(gilt["date"], dayfirst=True)
repo["Effective_Date"] = pd.to_datetime(repo["Effective_Date"], dayfirst=True)

# Convert numeric columns
corp["nav"] = corp["nav"].astype(float)
gilt["nav"] = gilt["nav"].astype(float)
repo["Repo_Rate_Percent"] = repo["Repo_Rate_Percent"].astype(float)

# Sort data
corp = corp.sort_values("date")
gilt = gilt.sort_values("date")
repo = repo.sort_values("Effective_Date")

# Normalize NAVs to Base 100
corp["nav_norm"] = corp["nav"] / corp["nav"].iloc[0] * 100
gilt["nav_norm"] = gilt["nav"] / gilt["nav"].iloc[0] * 100

# Normalize Repo Rate to Base 100
repo["repo_norm"] = repo["Repo_Rate_Percent"] / repo["Repo_Rate_Percent"].iloc[0] * 100

# ================== PLOT ==================
plt.figure(figsize=(14, 7))

# Plot all on SAME axis
plt.plot(corp["date"], corp["nav_norm"], label="ICICI Corporate Bond (Normalized)")
plt.plot(gilt["date"], gilt["nav_norm"], label="ICICI Gilt (Normalized)")
plt.plot(repo["Effective_Date"], repo["repo_norm"],
         linestyle="--", color="black", label="RBI Repo Rate (Normalized)")

# Labels
plt.xlabel("Date")
plt.ylabel("Normalized Value (Base = 100)")
plt.title("ICICI Bond vs Gilt NAV vs RBI Repo Rate (Single Axis, Base 100)")

# Legend on top center
plt.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, 1.02),
    ncol=3,
    frameon=False
)

plt.tight_layout()
plt.show()
