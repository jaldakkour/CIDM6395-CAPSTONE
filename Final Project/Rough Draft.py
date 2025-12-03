#This is where I will start entering the code to pull data from a small business 


import pandas as pd
import json

def transform_facebook_data(raw_data):
    if not raw_data:
        print("No raw data to transform.")
        return pd.DataFrame()

    # --- Step 1: Flatten the top level using json_normalize ---
    # This handles the main fields (message, created_time, ID, URL, shares)
    df = pd.json_normalize(
        raw_data,
        sep='_',  # Separator for nested keys (e.g., reactions_summary_total_count)
        errors='ignore'
    )

    # --- Step 2: Extract and flatten the nested 'Insights' ---
    # The 'insights' field is a list of metrics that needs to be pivoted.
    
    # Create a list to hold the flattened insights for merging
    insights_list = []
    
    for post in raw_data:
        # Get the insights list (it's under the key 'post_insights' due to aliasing in the extraction)
        insights = post.get('post_insights', {}).get('data', [])
        
        # We need the post ID to link the insights back to the original post
        post_id = post.get('id')
        
        # Initialize a dictionary for this post's insights
        post_insights = {'id': post_id}

        # Loop through the list of metrics (post_impressions_unique, etc.)
        for metric in insights:
            metric_name = metric.get('name')
            # The value is in a list of dictionaries; we only need the 'value' from the first element
            value = metric.get('values', [{}])[0].get('value')
            
            # Map the metric name to a clean column name and assign the value
            # Example: post_impressions_unique -> impressions_unique
            clean_name = metric_name.replace('post_', '') 
            post_insights[clean_name] = value

        insights_list.append(post_insights)

    # Convert the insights list to a DataFrame
    df_insights = pd.DataFrame(insights_list)

    # --- Step 3: Merge the two DataFrames ---
    # Merge the main post data with the insights data on the 'id' column
    final_df = pd.merge(df, df_insights, on='id', how='left')

    # --- Step 4: Final Cleanup and Reformatting ---
    
    # 1. Rename and clean up reaction/comment fields
    final_df = final_df.rename(columns={
        'reaction_summary_total_count': 'reactions_total',
        'comment_summary_total_count': 'comments_total',
        'shares_count': 'shares_total'
    })
    
    # 2. Select and reorder final columns for the database
    columns_to_keep = [
        'id', 'created_time', 'message', 'type', 'permalink_url',
        'reactions_total', 'comments_total', 'shares_total',
        'impressions_unique', 
        'engaged_users', 
        'consumptions_by_type' # This is still a dictionary, which we can handle later or now
    ]
    
    # Filter columns that actually exist after normalization
    final_columns = [col for col in columns_to_keep if col in final_df.columns]
    
    return final_df[final_columns]

# # Example usage (assuming raw_data was obtained from the extraction function):
# final_dataframe = transform_facebook_data(raw_data)
# print(final_dataframe.head())
