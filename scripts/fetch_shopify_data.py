import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

shopify_store = os.getenv("SHOPIFY_STORE")
shopify_access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")

def fetch_shopify_orders():
    try:
        url = f"https://{shopify_store}/admin/api/2023-01/orders.json?status=any&limit=250"
        headers = {
            "X-Shopify-Access-Token": shopify_access_token
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return pd.DataFrame()

        orders = response.json().get("orders", [])

        if not orders:
            print("⚠️ No orders found in Shopify.")
            return pd.DataFrame()

        df_orders = pd.json_normalize(orders)

        return df_orders

    except Exception as e:
        print(f"❌ Error fetching Shopify orders: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df_orders = fetch_shopify_orders()

    if not df_orders.empty:
        os.makedirs("data", exist_ok=True)
        df_orders.to_csv("data/shopify_orders.csv", index=False)
        print("✅ Shopify orders data saved successfully: data/shopify_orders.csv")
    else:
        print("⚠️ No data saved due to errors or empty response.")
