import pandas as pd

# Replace with your actual Google Sheet ID
SHEET_ID = "1FRIiadHaer7U7LgxN8CgdFRN1wCHURs1f9NjNNbcSp8"   

def fetch_google_sheets_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df = pd.read_csv(url)
    return df

if __name__ == "__main__":
    df_calls = fetch_google_sheets_data()
    print(df_calls.head())  # Preview data
    df_calls.to_csv("data/call_data.csv", index=False)
