import pandas as pd

def merge_data():
    df_calls = pd.read_csv("data/call_data.csv")

    df_orders = pd.read_csv("data/shopify_orders.csv")

    # Merge on 'email' (or any other common key)
    df_merged = df_calls.merge(df_orders, left_on="Email", right_on="email", how="left")
    
    df_merged.to_csv("data/merged_data.csv", index=False)
    print("✅ Merged data saved successfully!")

if __name__ == "__main__":
    merge_data()
