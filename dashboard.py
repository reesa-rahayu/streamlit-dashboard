import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set(style='dark')

# Function to convert to datetime datatype
def convert_date(df):
    # column need to convert
    datetime = ["order_purchase_timestamp","order_approved_at"]
    
    # change datatype to datetime
    for column in datetime:
        df[column] = pd.to_datetime(df[column])

    # get year from order_approved_at and add to order_year column
    all_df['order_year'] = all_df['order_approved_at'].dt.year
    
    # get hour from order_approved_at and add to order_hour column
    all_df['order_hour']= all_df['order_purchase_timestamp'].dt.hour

    # make order_period column
    time_bins = [0, 6, 12, 18, 24]
    time_labels = ['Night', 'Morning', 'Afternoon', 'Evening']
    all_df['order_period'] = pd.cut(all_df['order_hour'], bins=time_bins, labels=time_labels, right=False)

    return df

# Function to create needed dataframes
def create_monthly_orders_df(all_df):
    #Filter to recent year (2018)
    monthly_orders_df = all_df[all_df['order_year'] == 2018]

    # Aggregate by month
    monthly_orders_df = monthly_orders_df.resample(rule='ME', on='order_approved_at').agg({
        "order_id": "nunique",
        "payment_value": "sum",
    })

    # Change order_date to month
    monthly_orders_df.index = monthly_orders_df.index.strftime('%B')
    monthly_orders_df = monthly_orders_df.reset_index()

    # Rename column
    monthly_orders_df.rename(columns={
        "order_approved_at" : "month",
        "order_id": "order_count",
        "total_price": "revenue"
    }, inplace=True)

    # Return data
    return monthly_orders_df
def create_rfm_df(all_df):
    rfm_df = all_df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_purchase_timestamp": "max", # get last order timestamp
        "order_id": "nunique", # count order
        "payment_value": "sum" # count total payment
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    
    # count last transaction (minutes)
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"]
    recent_date = all_df["order_purchase_timestamp"].max()
    rfm_df["recency_minute"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).total_seconds() / 60)
    
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df
def create_top_categories_df(all_df):
    #filter to "delivered" order_status
    delivered_orders_df = all_df[all_df['order_status'] == 'delivered']

    # count order_count based on categories and order_year
    yearly_category_counts = delivered_orders_df.groupby(['order_year', 'product_category_name_english'])['order_id'].count().reset_index(name='order_count')

    # Look for top 5 categories
    top_categories = yearly_category_counts.groupby('order_year').head(5).reset_index(drop=True).sort_values(by=['order_year', 'order_count'], ascending=[False, False])

    return top_categories
def create_order_count_by_period(all_df):
    order_count_by_period = all_df.groupby('order_period', observed=False)['order_id'].count().reset_index(name='order_count')
    return order_count_by_period
def create_order_count_by_hour(all_df):
    order_count_by_hour = all_df.groupby('order_hour', observed=False)['order_id'].count().reset_index(name='order_count')
    return order_count_by_hour
def create_count_by_city(all_df):
    count_order_by_city = all_df.groupby(['customer_city', 'customer_state'], observed=False)['order_id'].count().reset_index(name='order_count')
    count_order_by_city.rename(columns={"customer_city": "city"}, inplace=True)
    return count_order_by_city
def create_count_by_state(all_df):   
    count_order_by_state = all_df.groupby('customer_state', observed=False)['order_id'].count().reset_index(name='order_count')
    count_order_by_state.rename(columns={"customer_state": "state"}, inplace=True)
    return count_order_by_state

# Load all_df data
all_df = pd.read_csv("all_data.csv")
#convert datatype
all_df = convert_date(all_df)

# Make df
monthly_orders_df = create_monthly_orders_df(all_df)
rfm_df = create_rfm_df(all_df)
top_categories_df = create_top_categories_df(all_df)
order_count_by_period = create_order_count_by_period(all_df)
order_count_by_hour = create_order_count_by_hour(all_df)
count_order_by_city = create_count_by_city(all_df)
count_order_by_state = create_count_by_state(all_df)

# Side Bar
with st.sidebar:
    st.subheader('Source:')
    st.markdown('[E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)')
    st.caption('Made with sincere by reesa.rahayu, 2024')

# Data Visualization
st.header('E-Commerce Public Dashboard :sparkles:')

# Define Color
fuchsia_color = "#FF00FF"

# Make tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Sales Performance", "Best Customer", "Top Categories", "Order by Time", "Order by Location"])
 
with tab1:
    st.header("Sales Performance")
    # Make column
    col1, col2 = st.columns(2)
    
    # Count Total Order and Payment 
    with col1:
        total_orders = monthly_orders_df.order_count.sum()
        st.metric("Total orders", value=total_orders)
    with col2:
        total_revenue = format_currency(monthly_orders_df.payment_value.sum(), "AUD", locale='es_CO') 
        st.metric("Total Payment", value=total_revenue)

    # Order Chart
    fig, ax = plt.subplots(figsize=(16, 8))
    plt.plot(monthly_orders_df["month"], monthly_orders_df["order_count"], marker='o', linewidth=4, color=fuchsia_color) 
    plt.title("Number of Order per Month (2018)", loc="center", fontsize=20) 
    plt.xticks(fontsize=10) 
    plt.yticks(fontsize=10) 
    plt.ylim(bottom=0) 
    st.pyplot(fig)

    # Payment Value Chart
    fig, ax = plt.subplots(figsize=(16, 8))
    plt.plot(monthly_orders_df["month"], monthly_orders_df["payment_value"], marker='o', linewidth=4, color=fuchsia_color) 
    plt.title("Number of Payment Value per Month (2018)", loc="center", fontsize=20) 
    plt.xticks(fontsize=10) 
    plt.yticks(fontsize=10) 
    plt.ylim(bottom=0) 
    st.pyplot(fig)

with tab2:
    st.header("Best Customer")
    st.subheader('Best Customer (RFM Analysis)')

    # Recency Plot
    fig1, ax1 = plt.subplots(figsize=(24, 10))
    colors = [fuchsia_color, fuchsia_color, fuchsia_color, fuchsia_color, fuchsia_color]
    sns.barplot(y="recency_minute", x="customer_id", hue="customer_id", legend=False, data=rfm_df.sort_values(by="recency_minute", ascending=True).head(5), palette=colors, ax=ax1)
    ax1.set_ylabel(None)
    ax1.set_xlabel(None)
    ax1.set_title("By Recency (minutes)", loc="center", fontsize=18)
    ax1.tick_params(axis='x', labelsize=15)
    st.pyplot(fig1)

    # Frecuency Plot
    fig2, ax2 = plt.subplots(figsize=(24, 10))
    colors = [fuchsia_color, fuchsia_color, fuchsia_color, fuchsia_color, fuchsia_color]
    sns.barplot(y="frequency", x="customer_id", hue="customer_id", legend=False, data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax2)
    ax2.set_ylabel(None)
    ax2.set_xlabel(None)
    ax2.set_title("By Frequency", loc="center", fontsize=18)
    ax2.tick_params(axis='x', labelsize=15)
    st.pyplot(fig2)

    # Monetary Plot
    fig3, ax3 = plt.subplots(figsize=(24, 10))
    colors = [fuchsia_color, fuchsia_color, fuchsia_color, fuchsia_color, fuchsia_color]
    sns.barplot(y="monetary", x="customer_id", hue="customer_id", legend=False, data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax3)
    ax3.set_ylabel(None)
    ax3.set_xlabel(None)
    ax3.set_title("By Monetary", loc="center", fontsize=18)
    ax3.tick_params(axis='x', labelsize=15)
    st.pyplot(fig3)
 
with tab3:
    st.header("Yearly Top Categories")

    # Make per year
    top_2016 = top_categories_df[top_categories_df['order_year'] == 2016].groupby(by=["order_year", "product_category_name_english"]).agg({
        "order_count": "sum"
    }).sort_values(by="order_count", ascending=False)

    top_2017 = top_categories_df[top_categories_df['order_year'] == 2017].groupby(by=["order_year", "product_category_name_english"]).agg({
        "order_count": "sum"
    }).sort_values(by="order_count", ascending=False)

    top_2018 = top_categories_df[top_categories_df['order_year'] == 2018].groupby(by=["order_year", "product_category_name_english"]).agg({
        "order_count": "sum"
    }).sort_values(by="order_count", ascending=False)

    # Make 2018 plot
    fig_2018, ax_2018 = plt.subplots(figsize=(8, 6))
    sns.barplot(x="order_count", y="product_category_name_english", data=top_2018, palette="Blues_r", ax=ax_2018)
    ax_2018.set_ylabel(None)
    ax_2018.set_xlabel("Order Count")
    ax_2018.set_title("Best Selling Categories 2018", fontsize=15)
    ax_2018.tick_params(axis='x')
    ax_2018.tick_params(axis='y', labelsize=12)
    st.pyplot(fig_2018)

    st.markdown("### **Insight:**")
    st.markdown("- The most popular category in 2018 is **Audio**")
    
    # Make 2017 plot
    fig_2017, ax_2017 = plt.subplots(figsize=(8, 6))
    sns.barplot(x="order_count", y="product_category_name_english", data=top_2017, palette="Blues_r", ax=ax_2017)
    ax_2017.set_ylabel(None)
    ax_2017.set_xlabel("Order Count")
    ax_2017.set_title("Best Selling Categories 2017", fontsize=15)
    ax_2017.tick_params(axis='x')
    ax_2017.tick_params(axis='y', labelsize=12)
    st.pyplot(fig_2017)

    st.markdown("### **Insight:**")
    st.markdown("- The most popular category in 2017 is **Audio**")

    # Makde 2016 plot
    fig_2016, ax_2016 = plt.subplots(figsize=(8, 6))
    sns.barplot(x="order_count", y="product_category_name_english", data=top_2016, palette="Blues_r", ax=ax_2016)
    ax_2016.set_ylabel(None)
    ax_2016.set_xlabel("Order Count")
    ax_2016.set_title("Best Selling Categories 2016", fontsize=15)
    ax_2016.tick_params(axis='x')
    ax_2016.tick_params(axis='y', labelsize=12)
    st.pyplot(fig_2016)

    st.markdown("### **Insight:**")
    st.markdown("- The most popular category in 2016 is **Baby**")

with tab4:
    st.header("Most Order by Time and Periode")

    # By Hour
    st.subheader("Most Order by Hour")
    fig, ax = plt.subplots(figsize=(16, 8))
    plt.plot(
        order_count_by_period["order_period"],
        order_count_by_period["order_count"],
        marker='o',
        linewidth=4,
        color=fuchsia_color 
    )
    plt.title("Most Order Traffic by Time Period", loc="center", fontsize=20)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.ylim(bottom=0) 
    st.pyplot(fig)

    st.markdown("### **Insight:**")
    st.markdown("- Our analysis shows that most purchasing activity occurs **between 10:00 and 22:00**, indicating a strong preference for daytime shopping among our customers.")

    # By Time Period Plot
    st.subheader("Most Order by Time Period")
    fig, ax = plt.subplots(figsize=(16, 8))
    plt.plot(
        order_count_by_hour["order_hour"],
        order_count_by_hour["order_count"],
        marker='o',
        linewidth=4,
        color=fuchsia_color 
    )
    plt.title("Most Order Traffic by Hour", loc="center", fontsize=20)
    plt.xticks(range(24),fontsize=10)
    plt.yticks(fontsize=10)
    plt.ylim(bottom=0) 
    st.pyplot(fig)

    st.markdown("### **Insight:**")
    st.markdown("- The highest volume of orders occurred during the *afternoon* period.")

with tab5:
    st.header('Most Order by Location')
    
    # By City
    st.subheader('By City')
    fig, ax = plt.subplots(figsize=(16, 8))
    colors_ = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
    sns.barplot(
        x="order_count", 
        y="city",
        hue="city",
        legend=False,
        data=count_order_by_city.sort_values(by="order_count", ascending=False).head(10),
        palette=colors_
    )
    plt.title("Number of Order by City", loc="center", fontsize=15)
    plt.ylabel(None)
    plt.xlabel(None)
    plt.tick_params(axis='y', labelsize=12)
    st.pyplot(fig)
    st.markdown("### **Insight:**")
    st.markdown("- The highest purchasing activity occurs in the **Sao Paulo, SP** city.")

    # By City
    st.subheader('By State')
    fig, ax = plt.subplots(figsize=(16, 8))
    colors2 = [fuchsia_color, fuchsia_color, fuchsia_color, fuchsia_color, fuchsia_color, fuchsia_color, fuchsia_color, fuchsia_color, fuchsia_color, fuchsia_color]
    sns.barplot(
        x="order_count", 
        y="state",
        hue="state",
        legend=False,
        data=count_order_by_state.sort_values(by="order_count", ascending=False).head(10),
        palette=colors2
    )
    plt.title("Number of Order by State", loc="center", fontsize=15)
    plt.ylabel(None)
    plt.xlabel(None)
    plt.tick_params(axis='y', labelsize=12)
    st.pyplot(fig)
    st.markdown("### **Insight:**")
    st.markdown("- The highest purchasing activity occurs in the state of **Sao Paulo (SP)**.")