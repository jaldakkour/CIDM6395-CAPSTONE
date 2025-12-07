import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os

# 1. Define the TEA_CATALOG (Use the large list provided in the previous response)
TEA_CATALOG = [
    # ... (Paste the entire list of 31 dictionaries here) ...
    {'Tea Name': 'Black Forest', 'Tea Type': 'Black', 'Flavor 1': 'Chocolate', 'Flavor 2': 'Cherry', 'Flavor 3': 'Cream', 'Antioxidant': 'High', 'Caffeine': 'Medium'},
    # ... (all 31 entries) ...
    {'Tea Name': 'Strawberry Immunity', 'Tea Type': 'Herbal/Berry', 'Flavor 1': 'Strawberry', 'Flavor 2': 'Tart Hibiscus', 'Flavor 3': 'Elderberry', 'Antioxidant': 'N/A', 'Caffeine': 'None'},
]

# 2. Database Connection (using your existing functions/credentials)
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

def create_mysql_connection(host, user, password, database_name):
    # Modified to connect directly to the database
    try:
        conn = mysql.connector.connect(
            host=host, user=user, password=password, database=database_name
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting: {err}")
        return None

# 3. Insertion Logic
def load_tea_catalog():
    # Use the database where the tea_catalog table will reside
    conn = create_mysql_connection(DB_HOST, DB_USER, DB_PASS, "ANALYTICS DATA (FAKE)") 
    if not conn:
        return

    cursor = conn.cursor()
    
    # Base SQL statement
    sql = """
    INSERT INTO `tea_catalog` (
        tea_name, tea_type, flavor_1, flavor_2, flavor_3, 
        flavor_4, flavor_5, antioxidant_level, caffeine_level
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    for tea in TEA_CATALOG:
        # Prepare data tuple, handling missing values and remapping column names
        data = (
            tea.get('Tea Name'),
            tea.get('Tea Type'),
            tea.get('Flavor 1', 'N/A'),
            tea.get('Flavor 2', 'N/A'),
            tea.get('Flavor 3', 'N/A'),
            tea.get('Flavor 4', 'N/A'), # Included for completeness, though often empty
            tea.get('Flavor 5', 'N/A'), # Included for completeness, though often empty
            tea.get('Antioxidant', 'N/A'),
            tea.get('Caffeine', 'N/A'),
        )
        try:
            cursor.execute(sql, data)
        except mysql.connector.Error as err:
            # Print error but continue to next row
            print(f"Error inserting {tea.get('Tea Name')}: {err}")
            
    conn.commit()
    cursor.close()
    conn.close()
    print("Tea catalog data loaded successfully.")

# Execute the loader
# load_tea_catalog()

