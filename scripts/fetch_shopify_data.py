import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

shopify_store = os.getenv("SHOPIFY_STORE")
shopify_access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")

def fetch_all_orders(since_id=None):
    all_orders = []
    base_url = f"https://{shopify_store}/admin/api/2023-01/orders.json"
    headers = {
        "X-Shopify-Access-Token": shopify_access_token
    }

    params = {
        "status": "any",
        "limit": 250,
        "order": "id asc"
    }

    if since_id:
        params["since_id"] = since_id

    while True:
        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            break

        batch = response.json().get("orders", [])
        if not batch:
            break

        all_orders.extend(batch)
        params["since_id"] = batch[-1]["id"]  # paginate by last order ID

        if len(batch) < 250:
            break  # end if less than 250 results returned

    return all_orders

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    csv_path = "data/shopify_orders.csv"

    # Load existing data if present
    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path)
        max_existing_id = existing_df["id"].max()
    else:
        existing_df = pd.DataFrame()
        max_existing_id = None

    new_orders = fetch_all_orders(since_id=max_existing_id)
    df_new = pd.json_normalize(new_orders)

    if df_new.empty and existing_df.empty:
        print("⚠️ No orders found in Shopify and no existing data.")
    else:
        combined_df = pd.concat([existing_df, df_new], ignore_index=True)
        combined_df.drop_duplicates(subset="id", keep="last", inplace=True)
        combined_df.to_csv(csv_path, index=False)
        print(f"✅ Shopify orders updated. Total records: {len(combined_df)}")
