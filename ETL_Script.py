import os
import requests
import pandas as pd
import numpy as np
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime, timedelta
# Note: Faker is not explicitly imported here but is assumed to be available
# if the generate_mock_sales_data function is used, and it was installed via pip.

# --- Initialization & Configuration ---
load_dotenv()
FACEBOOK_GRAPH_API = "https://graph.facebook.com/v19.0/"
SOCIAL_DB_NAME = "SOCIAL MEDIA DEMO"
ANALYTICS_DB_NAME = "ANALYTICS DATA (FAKE)"


# --- DB Connection Function (SS/DM) ---
def get_db_connection(database_name):
    """Establishes and returns a connection to the specified MySQL database."""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=database_name
        )
        print(f"Successfully connected to MySQL database: {database_name}")
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL database '{database_name}': {err}")
        return None

# --- Facebook Extraction Function (DM) ---
def extract_facebook_data(start_date, end_date, business_id):
    """Extracts high-level page/business metrics from Facebook over a time range."""
  # 1. RETRIEVE USER ACCESS TOKEN (LONG-LIVED) 
    user_access_token = os.getenv("FB_ACCESS_TOKEN")
    if not user_access_token:
        print("Error: FB_ACCESS_TOKEN not found in .env file.")
        return None

# 2. Fetch the Page Access Token using the User Token
    # This assumes the User has permissions to manage the page/business
    try:
        page_info_url = f"{FACEBOOK_GRAPH_API}{business_id}?fields=access_token&access_token={user_access_token}"
        page_response = requests.get(page_info_url)
        page_response.raise_for_status()
        page_data = page_response.json()
        
        # The Page Access Token is required for fetching insights
        page_access_token = page_data.get('access_token')
        
        if not page_access_token:
            print("Error: Could not retrieve Page Access Token using the User Token.")
            print(page_data)
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving Page Token: {e}")
        return None

# 2. Use the Page Access Token to fetch the insights (the main task)
    endpoint = f"{business_id}/insights"
    params = {
        'metric': 'page_posts_impressions,page_post_engagements',
        'period': 'day',
        'since': start_date.strftime("%Y-%m-%d"), 
        'until': end_date.strftime("%Y-%m-%d"),
        'access_token': page_access_token
    }
    url = FACEBOOK_GRAPH_API + endpoint
    
    try:
        print(f"Fetching data from Facebook API for {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        metrics_list = []
        if 'data' in data and data['data']:
            for metric in data['data']:
                metric_name = metric['name']
                for value_entry in metric.get('values', []):
                    # Ensure end_time is timezone-naive datetime object
                    end_time = pd.to_datetime(value_entry['end_time']).tz_localize(None)
                    
                    # Find existing entry or create new one for the date
                    date_exists = next((item for item in metrics_list if item['post_date'] == end_time), None)
                    
                    if not date_exists:
                        new_entry = {
                            'post_date': end_time,
                            'platform': 'Facebook',
                            'post_id': f"DAILY_AGG_{end_time.strftime('%Y%m%d')}",
                            'impressions': 0, 
                            'engagements': 0
                            # Missing columns will be set to None/0 in the load function
                        }
                        metrics_list.append(new_entry)
                        date_exists = new_entry
                        
                    # Add the metric value
                    if metric_name == 'page_posts_impressions':
                        date_exists['impressions'] += value_entry.get('value', 0)
                    elif metric_name == 'page_post_engagements':
                        date_exists['engagements'] += value_entry.get('value', 0)
            
            # Create DataFrame, ensuring required columns are present for the loader
            df = pd.DataFrame(metrics_list)
            if 'reach' not in df.columns: df['reach'] = 0
            if 'link_clicks' not in df.columns: df['link_clicks'] = 0
            if 'cost_usd' not in df.columns: df['cost_usd'] = None
            return df[['post_id', 'post_date', 'platform', 'reach', 'impressions', 'engagements', 'link_clicks', 'cost_usd']]
        else:
            print("API returned no data.")
            return pd.DataFrame()

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return None

# --- Mock Data Generation Function (DM/BA) ---
def generate_mock_sales_data(start_date, num_days):
    """Generates synthetic sales data for a specified period."""
    # Note: Faker is implicitly used for some internal randomness if it was needed, 
    # but the core logic relies on numpy/pandas.
    date_range = [start_date + timedelta(days=i) for i in range(num_days)]
    base_revenue = np.random.normal(loc=500, scale=100, size=num_days)
    is_social_day = np.random.choice([True, False], size=num_days, p=[0.3, 0.7])
    base_revenue[is_social_day] += np.random.normal(loc=300, scale=50, size=np.sum(is_social_day))

    data = {
        'sale_date': date_range,
        'revenue_usd': np.maximum(0, base_revenue).round(2),
        'items_sold': np.maximum(1, np.round(base_revenue / 100)),
        'source_channel': [np.random.choice(['social', 'direct', 'email', 'search'], p=[0.4, 0.3, 0.1, 0.2]) for _ in range(num_days)],
        'related_post_id': [None] * num_days 
    }
    return pd.DataFrame(data)

# --- Load Data Function (DM) ---
def load_data_to_mysql(df, table_name, database_name, is_sales=False):
    """Loads a Pandas DataFrame into a specified MySQL table."""
    conn = get_db_connection(database_name)
    if conn is None:
        return

    cursor = conn.cursor()
    
    if is_sales:
        # Columns must match the existing table: social_sales_fact
        columns = ['actual_sales_units', 'fake_post_id']
        placeholders = ', '.join(['%s'] * len(columns))
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        data_to_insert = [
          (
            row['items_sold'],
            str(row['related_post_id']) if pd.notna(row['related_post_id']) else ''
          )
          for index, row in df.iterrows()
         ]
    else: # social_metrics table
        columns = ['post_id', 'post_date', 'platform', 'reach', 'impressions', 'engagements', 'link_clicks', 'cost_usd']
        placeholders = ', '.join(['%s'] * len(columns))
        # Use ON DUPLICATE KEY UPDATE for social data, assuming post_id is PRIMARY KEY
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE impressions=VALUES(impressions), engagements=VALUES(engagements)"
        
        # Prepare data, ensuring all required columns exist in the DataFrame
        data_to_insert = []
        for index, row in df.iterrows():
             record = (
                row.get('post_id'),
                row.get('post_date'),
                row.get('platform'),
                row.get('reach', 0),
                row.get('impressions', 0),
                row.get('engagements', 0),
                row.get('link_clicks', 0),
                row.get('cost_usd', None)
            )
             data_to_insert.append(record)

    # Execute the batch insertion
    try:
        print(f"Loading {len(data_to_insert)} records into {database_name}.{table_name}...")
        cursor.executemany(sql, data_to_insert)
        conn.commit()
        print("Data loaded successfully.")
    except mysql.connector.Error as err:
        print(f"Error during data insertion: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


# --- Main Execution Block ---
if __name__ == '__main__':
    print("--- Starting ETL Pipeline: Conversion Compass ---")
    
    # Define the global date range for the project (90 days maximum)
    end_date = pd.Timestamp.now()
    # DATE RANGE FIXED TO 90 DAYS TO AVOID FACEBOOK API ERROR (400)
    data_days = 90 
    start_date = end_date - pd.Timedelta(days=data_days) 
    
    # --- PART 1: Real Social Media Data (Extraction and Load) ---
    business_id = os.getenv("FB_BUSINESS_ID")
    
    if business_id:
        facebook_df = extract_facebook_data(start_date, end_date, business_id)
        
        if facebook_df is not None and not facebook_df.empty:
            print("\n--- Loading Real Facebook Data ---")
            load_data_to_mysql(
                df=facebook_df,
                table_name='social_metrics',
                database_name=SOCIAL_DB_NAME
            )
        else:
             print("\nSkipping Facebook Data Load: Extraction failed or returned empty.")
    else:
        print("\nSkipping Facebook Extraction: FB_BUSINESS_ID not set in .env. Cannot retrieve real data.")


    # --- PART 2: Mock Sales Data (Generation and Load) ---
    print("\n--- Generating Mock Sales Data ---")
    mock_sales_df = generate_mock_sales_data(start_date, data_days)
    
    print("\n--- Loading Mock Sales Data ---")
    # Table name changed to match existing schema: social_sales_fact
    
    # Ensure DataFrame column names match the schema (sales_data)
    mock_sales_df.rename(columns={'sale_date': 'sale_date', 'revenue_usd': 'revenue_usd', 'items_sold': 'items_sold', 'source_channel': 'source_channel', 'related_post_id': 'related_post_id'}, inplace=True)

    load_data_to_mysql(
        df=mock_sales_df,
        table_name='social_sales_fact', # <-- FIX: Using your existing table name
        database_name=ANALYTICS_DB_NAME,
        is_sales=True
    )

    print("\nETL Pipeline Execution Complete.")

