import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
def load_data():
    file_path = "combined.csv"  # Update with actual file path if needed
    df = pd.read_csv(file_path, encoding='ISO-8859-1')
    df['Published_date_ist'] = pd.to_datetime(df['Published_date_ist'], errors='coerce')
    return df

df = load_data()

# Sidebar Filters
st.sidebar.header("Filters")
channel_options = df['Channel_title'].unique()
selected_channel = st.sidebar.multiselect("Select Channel(s)", channel_options, default=channel_options)
date_range = st.sidebar.date_input("Select Date Range", [df['Published_date_ist'].min(), df['Published_date_ist'].max()])

# Filter Data
df_filtered = df[
    (df['Channel_title'].isin(selected_channel)) & 
    (df['Published_date_ist'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))
]


# Main Dashboard
st.title("YouTube Analytics Dashboard")

# Line Chart: Views Over Time
fig_views = px.line(df_filtered, x='Published_date_ist', y='View_count', color='Channel_title', title='Views Over Time')
st.plotly_chart(fig_views)

# Bar Chart: Likes & Comments
fig_likes = px.bar(df_filtered, x='Published_date_ist', y=['Like_count', 'Comment_count'], color='Channel_title', title='Likes & Comments Over Time', barmode='group')
st.plotly_chart(fig_likes)

# Show Filtered Data Table
st.subheader("Filtered Data Table")
st.dataframe(df_filtered[['Published_date_ist', 'Channel_title', 'Title', 'View_count', 'Like_count', 'Comment_count']])
