import pandas as pd
import streamlit as st

# Set maximum cells for Pandas Styler rendering
pd.set_option("styler.render.max_elements", 500000)  # Set to a high value

source_df = pd.read_csv('source_pdpview_df.csv')




# Replace 0 ranks with max rank + 1
def replace_0_with_max_rank(df, rank_column, max_rank):
    df[rank_column] = df[rank_column].replace(0, max_rank+1)
    return df

# Function to calculate percentage difference
def percentage_diff(val1, val2, threshold=100):
    return (abs(val1 - val2) / threshold) * 100



# Sidebar for filters
st.sidebar.header("Filter Options")

# Category filter - using selectbox (default to "All")
category_options = ["All"] + source_df['category'].unique().tolist()
selected_category = st.sidebar.selectbox("Select Category", category_options)

# Threshold input
threshold = st.sidebar.number_input("Enter alignment threshold", min_value=0, max_value=10000, value=30)

# Top rank filter
top_rank = st.sidebar.number_input("Filter Top Ranks by", min_value=1, max_value=10000, value=100)

# Sorting options
sort_column = st.sidebar.selectbox("Sort by column", options=["fb_rank", "google_rank", "insta_rank", "cl_rank", "fb_views", "google_views", "insta_views", "cl_views"])
sort_order = st.sidebar.selectbox("Sort order", options=["Ascending", "Descending"])
ascending_order = True if sort_order == "Ascending" else False

# Filter the source_df based on the selected category
if selected_category != "All":
    filtered_df = source_df[source_df['category'] == selected_category]
else:
    filtered_df = source_df.copy()

# Create source-based DataFrames
fb_df = filtered_df[filtered_df['session_utm_source'].str.lower() == 'facebook'].copy()
fb_df = fb_df.groupby(['sku', 'session_utm_source'], as_index=False)['view_count'].sum()

google_df = filtered_df[filtered_df['session_utm_source'].str.lower() == 'google'].copy()
google_df = google_df.groupby(['sku', 'session_utm_source'], as_index=False)['view_count'].sum()

insta_df = filtered_df[filtered_df['session_utm_source'].str.lower() == 'instagram'].copy()
insta_df = insta_df.groupby(['sku', 'session_utm_source'], as_index=False)['view_count'].sum()

cl_df = filtered_df[filtered_df['session_utm_source'].str.lower() == 'caratlane'].copy()
cl_df = cl_df.groupby(['sku', 'session_utm_source'], as_index=False)['view_count'].sum()

# Rank by 'view_count'
fb_df['fb_rank'] = fb_df['view_count'].rank(method='dense', ascending=False)
google_df['google_rank'] = google_df['view_count'].rank(method='dense', ascending=False)
insta_df['insta_rank'] = insta_df['view_count'].rank(method='dense', ascending=False)
cl_df['cl_rank'] = cl_df['view_count'].rank(method='dense', ascending=False)

# Get the maximum ranks
fb_max_rank = fb_df['fb_rank'].max()
google_max_rank = google_df['google_rank'].max()
insta_max_rank = insta_df['insta_rank'].max()
cl_max_rank = cl_df['cl_rank'].max()

# Rename the view_count columns for clarity
fb_df.rename(columns={'view_count': 'fb_views'}, inplace=True)
google_df.rename(columns={'view_count': 'google_views'}, inplace=True)
insta_df.rename(columns={'view_count': 'insta_views'}, inplace=True)
cl_df.rename(columns={'view_count': 'cl_views'}, inplace=True)

# Merge the dataframes
merged_df = pd.merge(fb_df[['sku', 'fb_views', 'fb_rank']],
                     google_df[['sku', 'google_views', 'google_rank']],
                     on='sku', how='outer')

merged_df = pd.merge(merged_df,
                     insta_df[['sku', 'insta_views', 'insta_rank']],
                     on='sku', how='outer')

merged_df = pd.merge(merged_df,
                     cl_df[['sku', 'cl_views', 'cl_rank']],
                     on='sku', how='outer')

# Sort by selected column and order
merged_df = merged_df.sort_values(by=sort_column, ascending=ascending_order).reset_index(drop=True)

# Filter top N ranks based on user input
merged_df = merged_df[
    (merged_df['fb_rank'] <= top_rank) | 
    (merged_df['google_rank'] <= top_rank) | 
    (merged_df['insta_rank'] <= top_rank) | 
    (merged_df['cl_rank'] <= top_rank)
]

# Fill NaN values with 0 and replace 0 ranks with max rank + 1
merged_df = merged_df.fillna(0)
merged_df = replace_0_with_max_rank(merged_df, 'fb_rank', fb_max_rank)
merged_df = replace_0_with_max_rank(merged_df, 'google_rank', google_max_rank)
merged_df = replace_0_with_max_rank(merged_df, 'insta_rank', insta_max_rank)
merged_df = replace_0_with_max_rank(merged_df, 'cl_rank', cl_max_rank)


# Calculate percentage differences for alignment
merged_df['fb_google_diff'] = merged_df.apply(lambda row: percentage_diff(row['fb_rank'], row['google_rank']), axis=1)
merged_df['fb_insta_diff'] = merged_df.apply(lambda row: percentage_diff(row['fb_rank'], row['insta_rank']), axis=1)
merged_df['fb_cl_diff'] = merged_df.apply(lambda row: percentage_diff(row['fb_rank'], row['cl_rank']), axis=1)
merged_df['google_insta_diff'] = merged_df.apply(lambda row: percentage_diff(row['google_rank'], row['insta_rank']), axis=1)
merged_df['google_cl_diff'] = merged_df.apply(lambda row: percentage_diff(row['google_rank'], row['cl_rank']), axis=1)
merged_df['insta_cl_diff'] = merged_df.apply(lambda row: percentage_diff(row['insta_rank'], row['cl_rank']), axis=1)

# Highlighting function for top rank cells only
def highlight_top_rank_cells(row):
    styles = [''] * len(row)
    if row['fb_rank'] <= top_rank:
        styles[row.index.get_loc('fb_rank')] = 'background-color: yellow'
    if row['google_rank'] <= top_rank:
        styles[row.index.get_loc('google_rank')] = 'background-color: yellow'
    if row['insta_rank'] <= top_rank:
        styles[row.index.get_loc('insta_rank')] = 'background-color: yellow'
    if row['cl_rank'] <= top_rank:
        styles[row.index.get_loc('cl_rank')] = 'background-color: yellow'
    return styles

# Highlighting function for diff within threshold cells only
def highlight_threshold_diff_cells(row):
    styles = [''] * len(row)
    if row['fb_google_diff'] <= threshold:
        styles[row.index.get_loc('fb_google_diff')] = 'background-color: blue'
    if row['fb_insta_diff'] <= threshold:
        styles[row.index.get_loc('fb_insta_diff')] = 'background-color: blue'
    if row['fb_cl_diff'] <= threshold:
        styles[row.index.get_loc('fb_cl_diff')] = 'background-color: blue'
    if row['google_insta_diff'] <= threshold:
        styles[row.index.get_loc('google_insta_diff')] = 'background-color: blue'
    if row['google_cl_diff'] <= threshold:
        styles[row.index.get_loc('google_cl_diff')] = 'background-color: blue'
    if row['insta_cl_diff'] <= threshold:
        styles[row.index.get_loc('insta_cl_diff')] = 'background-color: blue'
    return styles

# Reset index on merged_df before applying styles
merged_df_reset = merged_df.reset_index(drop=True)

# Display the merged_df first with highlighted top rank cells
st.write("### Merged DataFrame")
# styled_merged_df = merged_df_reset.style.apply(highlight_top_rank_cells, axis=1).apply(highlight_threshold_diff_cells, axis=1)
styled_merged_df = merged_df_reset.style.apply(highlight_threshold_diff_cells, axis=1)
st.dataframe(styled_merged_df)

# Filter aligned rows within the threshold
aligned_fb_google = merged_df[merged_df['fb_google_diff'] <= threshold]
aligned_fb_insta = merged_df[merged_df['fb_insta_diff'] <= threshold]
aligned_fb_cl = merged_df[merged_df['fb_cl_diff'] <= threshold]
aligned_google_insta = merged_df[merged_df['google_insta_diff'] <= threshold]
aligned_google_cl = merged_df[merged_df['google_cl_diff'] <= threshold]
aligned_insta_cl = merged_df[merged_df['insta_cl_diff'] <= threshold]

# Select which aligned DataFrame to display
aligned_choice = st.sidebar.selectbox("Select aligned data to display", options=["fb_google", "fb_insta", "fb_cl", "google_insta", "google_cl", "insta_cl"])

# Map the choice to the correct DataFrame
aligned_dfs = {
    "fb_google": aligned_fb_google,
    "fb_insta": aligned_fb_insta,
    "fb_cl": aligned_fb_cl,
    "google_insta": aligned_google_insta,
    "google_cl": aligned_google_cl,
    "insta_cl": aligned_insta_cl
}

# Get the selected aligned DataFrame and reset the index
aligned_df = aligned_dfs[aligned_choice].reset_index(drop=True)

# Calculate and display overall alignment percentages
overall_align_fb_google = (len(aligned_fb_google) / len(merged_df)) * 100
overall_align_fb_insta = (len(aligned_fb_insta) / len(merged_df)) * 100
overall_align_fb_cl = (len(aligned_fb_cl) / len(merged_df)) * 100
overall_align_google_insta = (len(aligned_google_insta) / len(merged_df)) * 100
overall_align_google_cl = (len(aligned_google_cl) / len(merged_df)) * 100
overall_align_insta_cl = (len(aligned_insta_cl) / len(merged_df)) * 100


# Display overall alignment percentages
st.write(f"Overall alignment percentage for Facebook vs Google: {overall_align_fb_google:.2f}%")
st.write(f"Overall alignment percentage for Facebook vs Instagram: {overall_align_fb_insta:.2f}%")
st.write(f"Overall alignment percentage for Facebook vs CaratLane: {overall_align_fb_cl:.2f}%")
st.write(f"Overall alignment percentage for Google vs Instagram: {overall_align_google_insta:.2f}%")
st.write(f"Overall alignment percentage for Google vs CaratLane: {overall_align_google_cl:.2f}%")
st.write(f"Overall alignment percentage for Instagram vs CaratLane: {overall_align_insta_cl:.2f}%")

# Highlight top ranks in the aligned DataFrame
st.write(f"### Displaying aligned DataFrame: {aligned_choice}")
# styled_align_df = aligned_df.style.apply(highlight_top_rank_cells, axis=1).apply(highlight_threshold_diff_cells, axis=1)
styled_align_df = aligned_df.style.apply(highlight_threshold_diff_cells, axis=1)
st.dataframe(styled_align_df)






