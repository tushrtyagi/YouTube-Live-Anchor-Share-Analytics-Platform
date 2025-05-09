import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(page_title="YouTube Analytics Dashboard", layout="wide")

# Load data
def load_data():
    file_path = "./vod_data_all.csv"
    df = pd.read_csv(file_path, encoding='ISO-8859-1')
    df['Published_date_ist'] = pd.to_datetime(df['Published_date_ist'], errors='coerce')
    return df

# Load and prepare data
df = load_data()

# Sidebar Filters
st.sidebar.header("Filters")

# Date Range Filter
st.sidebar.subheader("Date Range Filter")
date_range = st.sidebar.date_input(
    "Select Date Range",
    [df['Published_date_ist'].min(), df['Published_date_ist'].max()]
)

# Channel Filter
st.sidebar.subheader("Channel Filter")
channel_options = df['Channel_title'].unique()
selected_channel = st.sidebar.multiselect(
    "Select Channel(s)",
    channel_options,
    default=channel_options
)

# View Count Filter
st.sidebar.subheader("View Count Filter")
min_views = int(df['View_count'].min())
max_views = int(df['View_count'].max())
view_range = st.sidebar.slider(
    "Select View Count Range",
    min_views, max_views,
    (min_views, max_views)
)

# Like Count Filter
st.sidebar.subheader("Like Count Filter")
min_likes = int(df['Like_count'].min())
max_likes = int(df['Like_count'].max())
like_range = st.sidebar.slider(
    "Select Like Count Range",
    min_likes, max_likes,
    (min_likes, max_likes)
)

# Filter Data
df_filtered = df[
    (df['Channel_title'].isin(selected_channel)) & 
    (df['Published_date_ist'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))) &
    (df['View_count'].between(view_range[0], view_range[1])) &
    (df['Like_count'].between(like_range[0], like_range[1]))
]

# Main Dashboard
st.title("YouTube Channel Analytics Dashboard")

# Overview Metrics
st.header("Overview Metrics")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Videos", len(df_filtered))
with col2:
    st.metric("Total Views", f"{df_filtered['View_count'].sum():,}")
with col3:
    st.metric("Total Likes", f"{df_filtered['Like_count'].sum():,}")

# Time series visualizations
st.header("Time Series Analysis")

# Views Over Time
st.subheader("Views Over Time by Channel")
daily_views = df_filtered.groupby(['Published_date_ist', 'Channel_title'])['View_count'].sum().reset_index()
fig_views = px.line(
    daily_views,
    x='Published_date_ist',
    y='View_count',
    color='Channel_title',
    title='Daily Views by Channel',
    labels={'Published_date_ist': 'Date', 'View_count': 'Views', 'Channel_title': 'Channel'}
)
fig_views.update_traces(mode='lines+markers')
st.plotly_chart(fig_views, use_container_width=True)

# Likes Over Time
st.subheader("Likes Over Time by Channel")
daily_likes = df_filtered.groupby(['Published_date_ist', 'Channel_title'])['Like_count'].sum().reset_index()
fig_likes = px.line(
    daily_likes,
    x='Published_date_ist',
    y='Like_count',
    color='Channel_title',
    title='Daily Likes by Channel',
    labels={'Published_date_ist': 'Date', 'Like_count': 'Likes', 'Channel_title': 'Channel'}
)
fig_likes.update_traces(mode='lines+markers')
st.plotly_chart(fig_likes, use_container_width=True)

# Channel-specific Analysis
st.header("Channel-specific Analysis")

# Create tabs for each channel
tabs = st.tabs(selected_channel)

for channel, tab in zip(selected_channel, tabs):
    with tab:
        channel_data = df_filtered[df_filtered['Channel_title'] == channel].copy()
        
        # Channel metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Channel Videos", len(channel_data))
        with col2:
            st.metric("Channel Views", f"{channel_data['View_count'].sum():,}")
        with col3:
            st.metric("Channel Likes", f"{channel_data['Like_count'].sum():,}")
        
        # Channel statistics
        st.subheader(f"Statistics for {channel}")
        stats_df = pd.DataFrame({
            'Metric': ['Average Views', 'Maximum Views', 'Average Likes', 'Maximum Likes',
                      'Average Like/View Ratio', 'Best Performing Video (Views)'],
            'Value': [
                f"{channel_data['View_count'].mean():,.0f}",
                f"{channel_data['View_count'].max():,}",
                f"{channel_data['Like_count'].mean():,.0f}",
                f"{channel_data['Like_count'].max():,}",
                f"{(channel_data['Like_count'].sum() / channel_data['View_count'].sum() * 100):.2f}%",
                channel_data.loc[channel_data['View_count'].idxmax(), 'Title']
            ]
        })
        st.dataframe(stats_df, use_container_width=True)
        
        # Detailed channel data
        st.subheader(f"Detailed Data for {channel}")
        channel_table = channel_data.sort_values('Published_date_ist', ascending=False)[
            ['Published_date_ist', 'Title', 'View_count', 'Like_count']
        ].reset_index(drop=True)
        channel_table['Published_date_ist'] = channel_table['Published_date_ist'].dt.strftime('%Y-%m-%d')
        st.dataframe(channel_table, use_container_width=True)

# Overall Summary Table
st.header("Overall Performance Summary")
summary_stats = df_filtered.groupby('Channel_title').agg({
    'View_count': ['count', 'sum', 'mean', 'max'],
    'Like_count': ['sum', 'mean', 'max']
}).round(2)

summary_stats.columns = [
    'Total Videos', 'Total Views', 'Avg Views', 'Max Views',
    'Total Likes', 'Avg Likes', 'Max Likes'
]
summary_stats = summary_stats.reset_index()
st.dataframe(summary_stats, use_container_width=True)

# Download button for filtered data
st.header("Export Data")
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df_to_csv(df_filtered)
st.download_button(
    "Download Filtered Data as CSV",
    csv,
    "youtube_analytics.csv",
    "text/csv",
    key='download-csv'
)