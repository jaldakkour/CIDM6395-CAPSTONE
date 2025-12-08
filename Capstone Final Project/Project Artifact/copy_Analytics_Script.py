import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import json
from datetime import timedelta

# --- 1. Configuration and Connection SetUp ---

# Load environment variables
load_dotenv()

# Database credentials
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

#FIX: Define unique variables for each database name
CATALOG_DB_NAME = "ANALYTICS DATA (FAKE)" #tea_catalog data
SOCIAL_DB_NAME = "SOCIAL MEDIA DEMO" #real facebook data

# --- ESTABLISH TWO SEPARATE MYSQL CONNECTIONS ---
# Connection 1: For Catalog/Inventory Data
try:
    catalog_conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=CATALOG_DB_NAME
    )
    print(f"Successfully connected to Catalog database: {CATALOG_DB_NAME}")
except mysql.connector.Error as err:
    print(f"Error connecting to Catalog DB: {err}")
    catalog_conn = None # Set to None if connection fails

# Connection 2: For Social Media Data
try:
    social_conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=SOCIAL_DB_NAME
    )
    print(f"Successfully connected to Social Media database: {SOCIAL_DB_NAME}")
except mysql.connector.Error as err:
    print(f"Error connecting to Social Media DB: {err}")
    social_conn = None # Set to None if connection fails

# If both fail, you might want to exit the script here.
if not catalog_conn and not social_conn:
    print("FATAL: Failed to connect to both required databases. Exiting.")
    exit()

# --- 2. MOCK DATA GENERATOR FUNCTIONS ---

def generate_mock_social_metrics(num_days, start_date):
    """Generates synthetic daily social metrics (Impressions/Engagements)."""
    dates = [start_date + timedelta(days=i) for i in range(num_days)]
    day_of_week = np.array([date.weekday() for date in dates])
    
    # Simulate higher metrics on weekends for correlation
    base_impressions = np.random.randint(1000, 5000, num_days)
    base_impressions[day_of_week >= 4] += 2000 
    
    base_engagements = np.random.randint(50, 250, num_days)
    base_engagements[day_of_week >= 4] += 100
    
    df_mock_social = pd.DataFrame({
        'post_date': dates,
        'daily_impressions': base_impressions,
        'daily_engagements': base_engagements
    })
    return df_mock_social

def generate_mock_flavor_data(num_days, start_date, tea_names_list):
    """Generates mock flavor sales and inventory data using a list of tea names."""
    dates = [start_date + timedelta(days=i) for i in range(num_days)]
    
    # 1. Create Sales Data
    data = []
    popular_tea = 'Organic Masala Chai' # Hardcoded popular tea for strong prediction demo
    
    for date in dates:
        for name in tea_names_list:
            base_sales = np.random.randint(2, 10)
            if name == popular_tea:
                base_sales += np.random.randint(5, 15) # Significant sales boost

            data.append({
                'sale_date': date,
                'tea_flavor': name,
                'units_sold': base_sales
            })
            
    # 2. Create Inventory Data (Randomly assigned starting inventory)
    inventory = {
        'tea_flavor': tea_names_list,
        'starting_inventory': np.random.randint(400, 700, len(tea_names_list)) 
    }
    
    df_sales = pd.DataFrame(data)
    df_inventory = pd.DataFrame(inventory)
    
    return df_sales, df_inventory

# --- 3. MAIN ANALYSIS EXECUTION ---

# Define the period constants (matching your ETL)
NUM_DAYS = 90
start_date = pd.to_datetime('2025-09-07') 

print("--- Starting Analysis: Conversion Compass Insights ---")

# --- ANALYSIS 1: SOCIAL IMPACT (Uses Mock Data) ---
print("\n--- Analysis 1: Social Media Impact (Charts 1 & 2) ---")

# 1. Generate Mock Data Sets 
df_mock_social = generate_mock_social_metrics(NUM_DAYS, start_date)

# 2. Generate Mock Sales Units (linked to mock social)
base_units = np.random.randint(10, 30, NUM_DAYS)
day_of_week = np.array([date.weekday() for date in df_mock_social['post_date']])
base_units[day_of_week >= 4] += 15 # Simulate correlation on weekends

df_mock_sales = pd.DataFrame({
    'post_date': df_mock_social['post_date'],
    'daily_units_sold': base_units
})

# 3. Join Mock Data Sets for Analysis 1
df = pd.merge(df_mock_social, df_mock_sales, on='post_date')

# Data Preparation
df['post_date'] = pd.to_datetime(df['post_date']).dt.date
df['daily_revenue'] = df['daily_units_sold'] * 50
print(f"Analysis 1 Data ready: {len(df)} daily records.")

# --- CHART 1: TIME-SERIES VISUALIZATION (Social Impact) ---
print("Generating Time-Series Visualization (Chart 1)...")
correlation = df['daily_engagements'].corr(df['daily_revenue'])
fig, ax1 = plt.subplots(figsize=(12, 6))

color = 'tab:blue'
ax1.set_xlabel('Date')
ax1.set_ylabel('Daily Engagements', color=color)
ax1.plot(df['post_date'], df['daily_engagements'], color=color, label='Engagements')
ax1.tick_params(axis='y', labelcolor=color)
ax2 = ax1.twinx()  # Secondary axis
color = 'tab:red'
ax2.set_ylabel('Daily Revenue (USD)', color=color)
ax2.plot(df['post_date'], df['daily_revenue'], color=color, linestyle='--', label='Revenue')
ax2.tick_params(axis='y', labelcolor=color)

plt.title(f'Social Engagements and Revenue Over Time (Correlation: {correlation:.2f})')
fig.tight_layout()
plt.grid(True, axis='y', linestyle=':', alpha=0.6)
plt.savefig('web/social_impact_time_series.png')
print("Saved chart: social_impact_time_series.png")

# --- EXPORT 1: TIME SERIES (Charts 1) ---
df_time_series_export = df[['post_date', 'daily_engagements', 'daily_revenue']].copy()
# Convert date objects to string for JSON compatibility
df_time_series_export['post_date'] = df_time_series_export['post_date'].astype(str)
df_time_series_export.to_json('web/time_series_data.json', orient='records', indent=4)
print("Exported: time_series_data.json (for Chart 1)")

# --- CHART 1.5: ACTUAL FACEBOOK ENGAGEMENTS (ETL PROOF) ---
print("Generating Actual Facebook Engagements Data (ETL Proof) from LIVE SQL...")

if social_conn:
    sql_query_facebook = """
    SELECT 
        post_date, 
        engagements AS total_engagements
    FROM 
        social_metrics
    ORDER BY 
        post_date;
    """
    
    try:
        df_facebook_proof = pd.read_sql_query(sql_query_facebook, social_conn)
        
        # Convert date to string for JSON output
        df_facebook_proof['post_date'] = df_facebook_proof['post_date'].astype(str)
        print(f"Successfully loaded {len(df_facebook_proof)} records from LIVE Facebook table.")
        # --- EXPORT 1.5: FACEBOOK ENGAGEMENTS (New Chart JSON) ---
        json_path_fb = 'web/facebook_engagements.json'
        df_facebook_proof.to_json(json_path_fb, orient='records', indent=4)
        print(f"Exported: facebook_engagements.json (for ETL Proof Chart) to {json_path_fb}")
     
    except Exception as e:
        print(f"Error executing SQL query for Facebook data: {e}")
else:
    print("Skipping Facebook Engagements Chart: Social Media database connection failed.")

# --- CHART 2: PREDICTIVE DAY OF WEEK ANALYSIS ---
print("Generating Day of Week Analysis (Chart 2)...")
df['day_name'] = pd.to_datetime(df['post_date']).dt.day_name()

daily_avg = df.groupby('day_name').agg(
    avg_revenue=('daily_revenue', 'mean')
).reset_index() 

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
daily_avg['day_name'] = pd.Categorical(daily_avg['day_name'], categories=day_order, ordered=True)
daily_avg = daily_avg.sort_values('day_name')

plt.figure(figsize=(10, 5))
sns.barplot(x='day_name', y='avg_revenue', data=daily_avg, palette='viridis', hue='day_name', legend=False)
plt.title('Predictive Insight: Average Predicted Sales Per Day')
plt.xlabel('Day of Week (Predicted Sales)')
plt.ylabel('Average Daily Revenue (USD)')
plt.grid(axis='y', linestyle=':', alpha=0.6)
plt.savefig('web/revenue_by_day_of_week.png')
print("Saved chart: revenue_by_day_of_week.png")

# --- EXPORT 2: DAY OF WEEK AVERAGE (Chart 2) ---
# 'daily_avg' DataFrame already exists from Chart 2 generation
daily_avg.to_json('web/day_of_week_avg_revenue.json', orient='records', indent=4)
print("Exported: day_of_week_avg_revenue.json (for Chart 2)")

# --- ANALYSIS 2: TEA FLAVOR (SQL-Driven) ---

print("\n--- Analysis 2: Tea Flavor and Inventory (Charts 3, 4, & 5) ---")
print("Integrating Tea Catalog Data via MySQL Query...")

if catalog_conn is None:
    print(f"FATAL: Could not connect to {CATALOG_DB_NAME}. Tea analysis skipped.")
    exit()

# SQL Query to pull the master tea catalog
sql_catalog_query = """
SELECT 
    tea_name, 
    tea_type, 
    flavor_1
FROM 
    tea_catalog;
"""

try:
    # Pull the catalog data directly into a DataFrame
    df_catalog = pd.read_sql(sql_catalog_query, catalog_conn)
    print(f"Successfully loaded {len(df_catalog)} tea catalog records.")

except Exception as e:
    print(f"Error executing SQL query for tea catalog: {e}")
    exit()

# 1. Generate Mock Sales and Inventory Data (Using names from the real catalog)
tea_names_from_catalog = df_catalog['tea_name'].tolist()

df_sales_detail, df_inventory = generate_mock_flavor_data(NUM_DAYS, start_date, tea_names_from_catalog)


# --- CHART 3: INVENTORY VS. SALES ---
print("Generating Inventory Analysis Chart (Chart 3)...")

# Aggregate sales by flavor
flavor_sales_summary = df_sales_detail.groupby('tea_flavor')['units_sold'].sum().reset_index()
flavor_sales_summary.rename(columns={'units_sold': 'total_units_sold'}, inplace=True)
inventory_analysis = pd.merge(df_inventory, flavor_sales_summary, on='tea_flavor', how='left')

inventory_analysis['ending_inventory'] = np.maximum(0, inventory_analysis['starting_inventory'] - inventory_analysis['total_units_sold'])

# --- INSERT THE INVENTORY DATA CONSTRAINT FIX HERE ---

# 1. Calculate the TOTAL inventory and TOTAL sales across ALL flavors
#    (These are the two figures used in your specific JSON output structure)
STARTING_INVENTORY_MAX = inventory_analysis['starting_inventory'].sum()
total_units_sold_figure = inventory_analysis['total_units_sold'].sum()

# 2. APPLY THE CONSTRAINT
if total_units_sold_figure > STARTING_INVENTORY_MAX:
    # If the calculated sold units are too high, cap the figure at the starting inventory max
    total_unit_sold_corrected = STARTING_INVENTORY_MAX
else:
    total_unit_sold_corrected = total_units_sold_figure

# 3. GENERATE THE CORRECTED JSON DATA DICTIONARY
inventory_analysis_data = {
    "chartTitle": "Inventory Management: Stock vs. Sales (Fixed)",
    "startingInventory": int( STARTING_INVENTORY_MAX),
    "totalUnitsSold": int(total_unit_sold_corrected),
    "remainingInventory": int(STARTING_INVENTORY_MAX - total_unit_sold_corrected)
}

# 4. SAVE THE CORRECTED JSON FILE
json_output_path = 'web/inventory_analysis.json'
with open(json_output_path, 'w') as f:
    json.dump(inventory_analysis_data, f, indent=4)

print(f"Corrected inventory analysis saved to {json_output_path}")

inventory_analysis.set_index('tea_flavor')[['starting_inventory', 'total_units_sold', 'ending_inventory']].plot(
    kind='bar', figsize=(14, 6), rot=45, 
    title='Inventory Management: Starting Stock, Sales, and Ending Stock by Flavor'
)
plt.ylabel('Units')
plt.xlabel('Tea Flavor')
plt.grid(axis='y', linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig('web/inventory_sales_comparison.png')
print("Saved chart: inventory_sales_comparison.png")

# --- EXPORT 3: INVENTORY ANALYSIS (Chart 3) ---
# 'inventory_analysis' DataFrame already exists from Chart 3 generation
inventory_analysis.to_json('web/inventory_analysis.json', orient='records', indent=4)
print("Exported: inventory_analysis.json (for Chart 3)")

# --- CHART 4: PREDICTIVE FLAVOR TREND ---
print("Generating Predictive Flavor Trend Chart (Chart 4)...")
daily_flavor_sales = df_sales_detail.groupby(['sale_date', 'tea_flavor'])['units_sold'].sum().unstack(fill_value=0)

# 1. Identify the top 5 flavors by total sales (using the existing flavor_sales_summary)
top_5_flavors = flavor_sales_summary.sort_values(
    'total_units_sold', ascending=False
).head(5)['tea_flavor'].tolist()

# 2. Filter the detailed sales data for only those top 5 flavors
daily_flavor_sales = df_sales_detail[
    df_sales_detail['tea_flavor'].isin(top_5_flavors)
].groupby(['sale_date', 'tea_flavor'])['units_sold'].sum().unstack(fill_value=0)

plt.figure(figsize=(12, 6))
daily_flavor_sales.plot(ax=plt.gca())
plt.title('Predictive Sales Trend: Daily Units Sold for Top 5 Tea Flavors (Fixed Clarity)')
plt.xlabel('Date')
plt.ylabel('Daily Units Sold')
plt.legend(title='Tea Flavor', bbox_to_anchor=(1.05, 1), loc='upper left') 
plt.grid(axis='y', linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig('web/flavor_sales_trend.png')
print("Saved chart: flavor_sales_trend.png (Chart 4 - Fixed)")

# --- CHART 5: COMBINED HISTORICAL & PREDICTIVE FLAVOR SALES (NEW REQUIREMENT) ---
print("Generating Combined Flavor Sales Chart (Chart 5)...")

# 1. Merge Sales Data with Catalog Data (to get Flavor 1)
df_merged_flavor = pd.merge(
    df_sales_detail, 
    df_catalog, 
    left_on='tea_flavor', 
    right_on='tea_name', 
    how='left'
)

# 2. Aggregate Historical Sales by Primary Flavor
historical_sales = df_merged_flavor.groupby('flavor_1')['units_sold'].sum().reset_index()
historical_sales.rename(columns={'units_sold': 'historical_units_sold'}, inplace=True)

# 3. Simulate Predictive Sales (For simplicity, predictions are historical sales + a random boost)
historical_sales['predicted_units_sold'] = (
    historical_sales['historical_units_sold'] * 1.05 +  # 5% baseline increase
    np.random.randint(50, 150, len(historical_sales))  # Random boost for 'prediction'
)
# Ensure predictions are positive
historical_sales['predicted_units_sold'] = np.maximum(0, historical_sales['predicted_units_sold'])

# 4. Combine and Sort (Top 10 based on Historical Sales)
combined_flavor_sales = historical_sales.sort_values(
    'historical_units_sold', ascending=False
)

top_combined_flavors = combined_flavor_sales[combined_flavor_sales['flavor_1'] != 'N/A'].head(10)

# --- CHART VISUALIZATION (Save PNG for fallback, JSON is for Chart.js) ---
plt.figure(figsize=(12, 6))
top_combined_flavors.set_index('flavor_1')[
    ['historical_units_sold', 'predicted_units_sold']
].plot(
    kind='barh', 
    figsize=(12, 6), 
    title='Top 10 Primary Flavors: Historical vs. Predicted Units Sold'
)
plt.xlabel('Total Units Sold (Historical & Predicted)')
plt.ylabel('Primary Flavor')
plt.grid(axis='x', linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig('web/combined_flavor_sales.png') # New PNG file name
print("Saved chart: combined_flavor_sales.png")

# --- EXPORT 4: COMBINED FLAVOR SALES (Chart 5 JSON) ---
# This JSON is for the HTML grouped bar chart
top_combined_flavors.to_json('web/flavor_sales_comparison.json', orient='records', indent=4)
print("Exported: flavor_sales_comparison.json (for Chart 5)")

# Close connections only if they were successfully established and are currently open
if catalog_conn and catalog_conn.is_connected():
    catalog_conn.close()
    print("Catalog database connection closed.")

if social_conn and social_conn.is_connected():
    social_conn.close()
    print("Social Media database connection closed.")

# ----------------------------------------------------------------------------------

print("\n--- ETL and Analysis Pipeline Complete ---")
