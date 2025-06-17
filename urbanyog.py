import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_extras.let_it_rain import rain
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.colored_header import colored_header
import datetime
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# PAGE CONFIG
st.set_page_config(
    page_title="Customer Call & Sales Dashboard",
    page_icon="📞",
    layout="wide"
)

# STYLE
st.markdown("""
    <style>
        body {
            background: linear-gradient(to bottom right, #fdfbfb, #ebedee);
        }
        h1, h2, h3 {
            color: #2d3436;
        }
        .stMetric {
            padding: 1rem 1rem;
            border-radius: 12px;
        }
    </style>
""", unsafe_allow_html=True)

# LOAD DATA
df = pd.read_csv("data/merged_data.csv")
df['StartTimestamp'] = pd.to_datetime(df['StartTimestamp'], errors='coerce')
df['call_date'] = df['StartTimestamp'].dt.date
df['title'] = df['title'].astype(str)

df['TotalCost'] = (
    df['TotalCost']
    .replace('-', '0')
    .replace('[\$,]', '', regex=True)
    .astype(float)
    * 85
)

df['TotalDuration (in sec)'] = pd.to_numeric(df['TotalDuration (in sec)'], errors='coerce').fillna(0)

call_data = pd.read_csv("data/call_data.csv")
call_data['StartTimestamp'] = pd.to_datetime(call_data['StartTimestamp'], errors='coerce')
call_data['call_date'] = call_data['StartTimestamp'].dt.date
call_data['TotalDuration (in sec)'] = pd.to_numeric(call_data['TotalDuration (in sec)'], errors='coerce').fillna(0)

# --------- SIDEBAR FILTERS ---------
with st.sidebar:
    st.header("🗓️ Filter Date Range")
    start_date = st.date_input("Start Date", df['call_date'].min())
    end_date = st.date_input("End Date", df['call_date'].max())
    st.markdown("---")
    st.info("Use the filters above to customize the dashboard view!")

df_filtered = df[(df['call_date'] >= start_date) & (df['call_date'] <= end_date)].copy()

# Merge COGS
cogs_df = pd.read_excel("data/UrbanYog_COGS.xlsx")
cogs_df['Product Purchased'] = cogs_df['NAME'].astype(str).str.strip().str.lower()
df_filtered['title_clean'] = df_filtered['title'].str.strip().str.lower()
df_filtered = df_filtered.merge(cogs_df[['Product Purchased', 'COGS']], left_on="title_clean", right_on="Product Purchased", how="left")

picked_up_calls = call_data[
    (call_data['call_date'] >= start_date) &
    (call_data['call_date'] <= end_date) &
    (call_data['TotalDuration (in sec)'] > 1)
]

# METRICS
st.title("Urban Voice Agent Dashboard")

total_calls = len(df_filtered)
connected_calls = len(picked_up_calls)
total_call_cost = df_filtered['TotalCost'].sum()
total_call_duration_sec = df_filtered['TotalDuration (in sec)'].sum()
total_call_duration_hms = str(datetime.timedelta(seconds=int(total_call_duration_sec)))

# Dynamic Metrics Init
total_purchases = 0
conversion = 0
total_revenue = 0
total_cogs_value = 0
profit_amount = 0

# First Row
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📞 Total Calls", total_calls if total_calls > 0 else "0")
col2.metric("✅ Connected Calls", connected_calls if connected_calls > 0 else "0")
col3_placeholder = col3.empty()
col4_placeholder = col4.empty()
col5.metric("📞 Total Call Cost (INR)", f"₹{total_call_cost:,.2f}" if total_call_cost > 0 else "₹0.00")

# Second Row
col6, col7, col8, col9 = st.columns(4)
col6.metric("⏱️ Total Call Duration", total_call_duration_hms if total_call_duration_sec > 0 else "0:00:00")
col7_placeholder = col7.empty()

style_metric_cards()

# CALL DURATION HISTOGRAM
colored_header("⏳ Call Duration", "", color_name="blue-70")
fig2 = px.histogram(df_filtered, x="DurationSeconds", nbins=20, title="Duration Histogram", color_discrete_sequence=["#00b894"])
st.plotly_chart(fig2, use_container_width=True)

# 👤 CUSTOMERS WHO MADE A PURCHASE
colored_header("👤 Customers Who Made a Purchase", "", color_name="gray-70")

try:
    timestamp_column = None
    for col in df_filtered.columns:
        if 'created' in col.lower() and 'at' in col.lower():
            timestamp_column = col
            break

    customer_df = df_filtered[df_filtered['order_number'].notna()][['call_date', 'Email', 'order_number', 'title']].drop_duplicates()

    if not customer_df.empty and timestamp_column:
        customer_df_full = df_filtered[df_filtered['order_number'].notna()][
            ['call_date', 'Email', 'order_number', timestamp_column, 'StartTimestamp', 'title', 'total_price', 'COGS']
        ].copy()

        customer_df_full['StartTimestamp'] = pd.to_datetime(customer_df_full['StartTimestamp'], errors='coerce')
        customer_df_full[timestamp_column] = pd.to_datetime(customer_df_full[timestamp_column], errors='coerce')
        customer_df_full['StartTimestamp'] = customer_df_full['StartTimestamp'].dt.tz_localize(None)
        customer_df_full[timestamp_column] = customer_df_full[timestamp_column].dt.tz_localize(None)

        customer_df_full = customer_df_full[customer_df_full['StartTimestamp'] <= customer_df_full[timestamp_column]]
        customer_df_full['Order Time'] = customer_df_full[timestamp_column].dt.strftime('%Y-%m-%d %H:%M:%S')
        customer_df_full['Call Time'] = customer_df_full['StartTimestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        customer_df_full = customer_df_full.sort_values('StartTimestamp')
        customer_df_full = customer_df_full.drop_duplicates(subset='Email', keep='first')

        customer_df_full = customer_df_full.rename(columns={
            "call_date": "Date",
            "Email": "Customer Email",
            "order_number": "Order Number",
            "title": "Product Purchased",
            "total_price": "Price"
        })[["Date", "Customer Email", "Order Number", "Call Time", "Order Time", "Product Purchased", "Price", "COGS"]]

        st.dataframe(customer_df_full, use_container_width=True)

        # METRICS
        total_purchases = customer_df_full['Customer Email'].nunique()
        conversion = round(total_purchases / connected_calls * 100, 2) if connected_calls > 0 else 0
        total_revenue = customer_df_full['Price'].sum()
        total_cogs_value = customer_df_full['COGS'].sum()
        profit_amount = ((total_revenue / 118) * 100) - total_cogs_value - total_call_cost - (120 * total_purchases)

        col3_placeholder.metric("👝 Purchases", total_purchases if total_purchases > 0 else "0")
        col4_placeholder.metric("🔀 Conversion", f"{conversion}%" if conversion > 0 else "0%")
        col7_placeholder.metric("💰 Total Revenue", f"₹{total_revenue:,.2f}" if total_revenue > 0 else "₹0.00")
        col8.metric("📦 Total COGS Price", f"₹{total_cogs_value:,.2f}" if total_cogs_value > 0 else "₹0")
        col9.metric("💸 Profit Amount", f"₹{profit_amount:,.2f}" if profit_amount > 0 else "₹0")

        # PIE CHART
        if not customer_df_full.empty:
            colored_header("Product Purchased Distribution", "", color_name="green-70")

            product_purchase_dist = customer_df_full['Product Purchased'].value_counts().reset_index()
            product_purchase_dist.columns = ['Product', 'Count']

            fig_product_buyer = px.pie(
                product_purchase_dist,
                names='Product',
                values='Count',
                hole=0.4,
                title="Product Purchased by Customers Who Made a Purchase",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_product_buyer, use_container_width=True)
    else:
        st.info("No customer purchase data found in the selected date range.")
        col8.metric("📦 Total COGS Price", "₹0")

except Exception as e:
    st.error(f"⚠️ An error occurred while loading purchase data: `{str(e)}`")

# AGENT LEADERBOARD
if 'Agent' in df_filtered.columns:
    colored_header("🏆 Top Performing Agents", "", color_name="orange-70")
    leaderboard = df_filtered.groupby('Agent')['order_number'].count().sort_values(ascending=False).reset_index()
    leaderboard.columns = ['Agent', 'Purchases']
    st.dataframe(leaderboard.style.highlight_max(axis=0, color='lightgreen'), use_container_width=True)

# OFF5 COUPON SECTION
colored_header("🏷️ OFF5 Coupon Used", "", color_name="red-70")

off5_mask = df_filtered['discount_codes'].astype(str).str.contains("OFF5", case=False, na=False)
off5_df = df_filtered[off5_mask].copy()

if not off5_df.empty:
    def extract_off5_code(discounts):
        try:
            data = eval(discounts) if isinstance(discounts, str) else discounts
            if isinstance(data, list):
                for d in data:
                    if d.get('code', '').upper() == 'OFF5':
                        return d.get('code')
        except:
            return None
        return None

    off5_df['Coupon Code'] = off5_df['discount_codes'].apply(extract_off5_code)
    off5_table = off5_df[['customer.first_name', 'customer.email', 'order_number', 'Coupon Code']].dropna().drop_duplicates()
    off5_table.columns = ['Customer Name', 'Customer Email', 'Order Number', 'Coupon Code']

    st.dataframe(off5_table, use_container_width=True)
    st.download_button("⬇️ Export OFF5 Coupon Data", data=off5_table.to_csv(index=False), file_name="off5_coupon_customers.csv", mime="text/csv")
else:
    st.info("No 'OFF5' coupon usage found in the selected date range.")
