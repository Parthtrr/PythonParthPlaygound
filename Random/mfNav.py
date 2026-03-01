import requests
from bs4 import BeautifulSoup
import pandas as pd

urls = {
    "ICICI_Corp_Bond": "https://www.advisorkhoj.com/mutual-funds-research/historical-NAV/ICICI%20Pru%20Corp%20Bond%20Gr?start_date=22-02-2016&end_date=21-01-2026",
    "ICICI_Gilt": "https://www.advisorkhoj.com/mutual-funds-research/historical-NAV/ICICI%20Pru%20Gilt%20Gr?start_date=22-02-2016&end_date=21-01-2026"
}

headers = {
    "User-Agent": "Mozilla/5.0"
}

def scrape_nav(url):
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    table = soup.find("table")
    rows = table.find_all("tr")

    data = []
    for row in rows[1:]:
        cols = [c.text.strip() for c in row.find_all("td")]
        if cols:
            data.append(cols)

    df = pd.DataFrame(data, columns=["date", "nav"])
    return df

# Create Excel with multiple sheets
with pd.ExcelWriter("icici_funds_nav.xlsx", engine="openpyxl") as writer:
    for sheet_name, url in urls.items():
        df = scrape_nav(url)
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print("Excel file created: icici_funds_nav.xlsx")
