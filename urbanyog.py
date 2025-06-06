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

# Convert '$' TotalCost to float and then INR
df['TotalCost'] = (
    df['TotalCost']
    .replace('-', '0')
    .replace('[\$,]', '', regex=True)
    .astype(float)
    * 85
)

# Clean and convert TotalDuration (in sec)
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

# Apply the date filter
df_filtered = df[(df['call_date'] >= start_date) & (df['call_date'] <= end_date)]

# Filter picked-up calls
picked_up_calls = call_data[
    (call_data['call_date'] >= start_date) &
    (call_data['call_date'] <= end_date) &
    (call_data['TotalDuration (in sec)'] > 1)
]

# Prepare customer_df and metric
customer_df = df_filtered[df_filtered['order_number'].notna()][['call_date', 'Email', 'order_number', 'title']].drop_duplicates()
total_purchases = len(customer_df)

# METRICS
st.title("UrbanYog Voice Agent Dashboard")

total_calls = len(df_filtered)
connected_calls = len(picked_up_calls)
conversion = round(total_purchases / connected_calls * 100, 2) if connected_calls > 0 else 0
total_call_cost = df_filtered['TotalCost'].sum()
total_call_duration_sec = df_filtered['TotalDuration (in sec)'].sum()
total_call_duration_hms = str(datetime.timedelta(seconds=int(total_call_duration_sec)))

# ✅ Calculate revenue from unique orders
total_revenue = (
    df_filtered.drop_duplicates(subset='order_number')['total_line_items_price']
    .dropna()
    .sum()
)

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
col1.metric("📞 Total Calls", total_calls)
col2.metric("✅ Connected Calls", connected_calls)
col3.metric("🛍️ Purchases", total_purchases)
col4.metric("💯 Conversion", f"{conversion}%")
col5.metric("📞 Total Call Cost (INR)", f"₹{total_call_cost:,.2f}")
col6.metric("⏱️ Total Call Duration", total_call_duration_hms)
col7.metric("💰 Total Revenue", f"₹{total_revenue:,.2f}")

style_metric_cards()

# CONFETTI + AUDIO
if conversion > 40:
    rain(
        emoji="🎉",
        font_size=40,
        falling_speed=5,
        animation_length="infinite",
    )
    st.audio("https://actions.google.com/sounds/v1/alarms/medium_bell_ring.ogg")

# --- PRODUCT PURCHASED PIE CHART ---
if not customer_df.empty and 'title' in customer_df.columns:
    colored_header("Product Purchased Distribution", "", color_name="green-70")
    product_counts = customer_df['title'].value_counts().reset_index()
    product_counts.columns = ['Product', 'Count']
    fig_product = px.pie(
        product_counts, names='Product', values='Count', hole=0.4,
        title="Product Purchased",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig_product, use_container_width=True)

# CALLS VS PURCHASES BAR CHART
colored_header("📊 Calls vs Purchases", "", color_name="violet-70")
df_grouped = df_filtered.groupby('call_date')['order_number'].count().reset_index()
fig1 = px.bar(df_grouped, x="call_date", y="order_number", title="Daily Purchases", color_discrete_sequence=["#6c5ce7"])
st.plotly_chart(fig1, use_container_width=True)

# CALL DURATION HISTOGRAM
colored_header("⏳ Call Duration", "", color_name="blue-70")
fig2 = px.histogram(df_filtered, x="DurationSeconds", nbins=20, title="Duration Histogram", color_discrete_sequence=["#00b894"])
st.plotly_chart(fig2, use_container_width=True)

# DISCONNECTION REASONS
st.subheader("📞 Disconnection Reasons")
fig = px.bar(df_filtered, x="DisconnectionReason", title="Disconnection Reasons Breakdown")
st.plotly_chart(fig, use_container_width=True)

# CALL OUTCOMES
if 'CallSuccessful' in df_filtered.columns:
    colored_header("🎯 Call Outcome", "", color_name="yellow-70")
    outcome_counts = df_filtered['CallSuccessful'].value_counts().reset_index()
    outcome_counts.columns = ['Status', 'Count']
    fig5 = px.bar(outcome_counts, x="Status", y="Count", color="Status", text="Count", color_discrete_map={0: "red", 1: "green"})
    fig5.update_traces(texttemplate='%{text}', textposition='outside')
    st.plotly_chart(fig5, use_container_width=True)

# AGENT LEADERBOARD
if 'Agent' in df_filtered.columns:
    colored_header("🏆 Top Performing Agents", "", color_name="orange-70")
    leaderboard = df_filtered.groupby('Agent')['order_number'].count().sort_values(ascending=False).reset_index()
    leaderboard.columns = ['Agent', 'Purchases']
    st.dataframe(leaderboard.style.highlight_max(axis=0, color='lightgreen'), use_container_width=True)

# CUSTOMERS WHO MADE A PURCHASE
colored_header("👤 Customers Who Made a Purchase", "", color_name="gray-70")

# Try to identify the order timestamp column
timestamp_column = None
for col in df_filtered.columns:
    if 'created' in col.lower() and 'at' in col.lower():
        timestamp_column = col
        break

if not customer_df.empty and timestamp_column:
    customer_df_full = df_filtered[df_filtered['order_number'].notna()][
        ['call_date', 'Email', 'order_number', timestamp_column, 'StartTimestamp', 'title', 'total_line_items_price']
    ].copy()

    customer_df_full[timestamp_column] = pd.to_datetime(customer_df_full[timestamp_column], errors='coerce')
    customer_df_full['Order Time'] = customer_df_full[timestamp_column].dt.strftime('%Y-%m-%d %H:%M:%S')
    customer_df_full['StartTimestamp'] = pd.to_datetime(customer_df_full['StartTimestamp'], errors='coerce')
    customer_df_full['Call Time'] = customer_df_full['StartTimestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

    customer_df_full = customer_df_full.sort_values('StartTimestamp').drop_duplicates(subset='order_number', keep='first')

    customer_df_full = customer_df_full.rename(columns={
        "call_date": "Date",
        "Email": "Customer Email",
        "order_number": "Order Number",
        "title": "Product Purchased",
        "total_line_items_price": "Price"
    })[["Date", "Customer Email", "Order Number", "Call Time", "Order Time", "Product Purchased", "Price"]]

    st.dataframe(customer_df_full, use_container_width=True)

elif not customer_df.empty:
    st.warning("⚠️ Could not detect a valid order time column.")
    customer_df_simple = df_filtered[df_filtered['order_number'].notna()][
        ['call_date', 'Email', 'order_number', 'title', 'total_line_items_price']
    ].drop_duplicates()

    customer_df_simple = customer_df_simple.rename(columns={
        "call_date": "Date",
        "Email": "Customer Email",
        "order_number": "Order Number",
        "title": "Product Purchased",
        "total_line_items_price": "Price"
    })[["Date", "Customer Email", "Order Number", "Product Purchased", "Price"]]

    st.dataframe(customer_df_simple, use_container_width=True)

else:
    st.info("No customer purchase data found in the selected date range.")

# DOWNLOAD FILTERED DATA
st.markdown("## 📁 Download Filtered Data")
st.download_button("⬇️ Download Filtered CSV", data=df_filtered.to_csv(index=False), file_name="filtered_data.csv", mime="text/csv")

# OFF5 COUPON USED
colored_header("🏷️ OFF5 Coupon Used", "", color_name="red-70")
off5_mask = df_filtered['discount_codes'].astype(str).str.contains("OFF5", case=False, na=False)
off5_df = df_filtered[off5_mask]

if not off5_df.empty:
    off5_table = df_filtered[['customer.first_name', 'customer.email', 'order_number']].dropna().drop_duplicates()
    off5_table.columns = ['Customer Name', 'Customer Email', 'Order Number']
    st.dataframe(off5_table, use_container_width=True)

    st.download_button(
        label="⬇️ Export OFF5 Coupon Data",
        data=off5_table.to_csv(index=False),
        file_name="off5_coupon_customers.csv",
        mime="text/csv"
    )
else:
    st.info("No 'OFF5' coupon usage found in the selected date range.")
