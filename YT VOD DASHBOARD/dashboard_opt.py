import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import time
import os

# MySQL Database Configuration
hostname = "database-2.c9asogtdnypd.ap-south-1.rds.amazonaws.com"
dbname = "youtube_db4"
uname = "admin"
pwd = "SocialMkt22"

# Create a connection to the database with connection pooling and timeout settings
def get_db_connection():
    # Add connection pool recycle and timeout parameters
    connection_string = f"mysql+pymysql://{uname}:{pwd}@{hostname}/{dbname}?charset=utf8"
    engine = create_engine(
        connection_string,
        pool_recycle=3600,  # Recycle connections after 1 hour
        connect_args={
            "connect_timeout": 60,  # Connection timeout in seconds
            "read_timeout": 120,     # Read timeout in seconds
        }
    )
    return engine

# Load data from MySQL with retry mechanism and chunking
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    max_retries = 10
    chunk_size = 10000 # Adjust based on your data size
    
    # Try loading from CSV cache first if exists
    cache_file = "data_cache.csv"
    if os.path.exists(cache_file):
        try:
            df = pd.read_csv(cache_file)
            df['Published_date_ist'] = pd.to_datetime(df['Published_date_ist'], errors='coerce')
            return df
        except Exception as e:
            st.warning(f"Could not load from cache: {e}")
    
    # If cache doesn't exist or failed to load, fetch from database
    for attempt in range(max_retries):
        try:
            engine = get_db_connection()
            
            # Use chunking to avoid large query timeouts
            chunks = []
            offset = 0
            while True:
                query = f"SELECT * FROM Daliy_vod_inc LIMIT {chunk_size} OFFSET {offset}"
                chunk = pd.read_sql(query, engine)
                
                if chunk.empty:
                    break
                    
                chunks.append(chunk)
                offset += chunk_size
                
                # Break if we've loaded enough data
                if offset >= 2000:
                    break
            
            if not chunks:
                return pd.DataFrame()
                
            df = pd.concat(chunks, ignore_index=True)
            df['Published_date_ist'] = pd.to_datetime(df['Published_date_ist'], errors='coerce')
            
            # Ensure numeric conversion for View_count and Like_count
            df['View_count'] = pd.to_numeric(df['View_count'], errors='coerce')
            df['Like_count'] = pd.to_numeric(df['Like_count'], errors='coerce')
            df['View_count'].fillna(0, inplace=True)
            df['Like_count'].fillna(0, inplace=True)
            
            # Save to cache for future use
            try:
                df.to_csv(cache_file, index=False)
            except Exception as e:
                st.warning(f"Could not save to cache: {e}")
                
            return df
                
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"Database connection failed (attempt {attempt+1}). Retrying...")
                time.sleep(2)  # Wait before retrying
            else:
                st.error(f"Failed to load data after {max_retries} attempts: {e}")
                # Return empty DataFrame as fallback
                return pd.DataFrame()

# Alert about connection issues
try:
    st.info("Loading data from database... This may take a moment.")
    # Load and prepare data
    df = load_data()
    if df.empty:
        st.error("Could not load data from the database. Please check your connection and try again.")
        st.stop()
except Exception as e:
    st.error(f"Error initializing the application: {e}")
    st.stop()

# Sidebar Filters
st.sidebar.header("Filters")

# Date Range Filter
st.sidebar.subheader("Date Range Filter")
min_date = df['Published_date_ist'].min() if not df.empty else pd.Timestamp.now()
max_date = df['Published_date_ist'].max() if not df.empty else pd.Timestamp.now()
date_range = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date]
)

# Channel Filter
st.sidebar.subheader("Channel Filter")
channel_options = df['Channel_title'].unique() if not df.empty else []
selected_channel = st.sidebar.multiselect(
    "Select Channel(s)",
    channel_options,
    default=channel_options
)

# View Count Filter
st.sidebar.subheader("View Count Filter")
min_views = int(df['View_count'].min()) if not df.empty else 0
max_views = int(df['View_count'].max()) if not df.empty else 1000
view_range = st.sidebar.slider(
    "Select View Count Range",
    min_views, max_views,
    (min_views, max_views)
)

# Like Count Filter
st.sidebar.subheader("Like Count Filter")
min_likes = int(df['Like_count'].min()) if not df.empty else 0
max_likes = int(df['Like_count'].max()) if not df.empty else 1000
like_range = st.sidebar.slider(
    "Select Like Count Range",
    min_likes, max_likes,
    (min_likes, max_likes)
)

# Filter Data
if not df.empty:
    df_filtered = df[
        (df['Channel_title'].isin(selected_channel)) & 
        (df['Published_date_ist'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))) & 
        (df['View_count'].between(view_range[0], view_range[1])) & 
        (df['Like_count'].between(like_range[0], like_range[1]))
    ]
else:
    df_filtered = df

# Main Dashboard
st.title("YouTube Channel Analytics Dashboard")

if df_filtered.empty:
    st.warning("No data available with the current filters or connection to database failed.")
    st.stop()

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

# Individual Channel Analysis with tabs for channel selection
st.header("Channel-specific Analysis")

# Create tabs for each channel
if selected_channel:
    channel_tabs = st.tabs(selected_channel)

    for i, tab in enumerate(channel_tabs):
        channel = selected_channel[i]
        with tab:
            channel_data = df_filtered[df_filtered['Channel_title'] == channel]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Videos", len(channel_data))
            with col2:
                st.metric("Total Views", f"{channel_data['View_count'].sum():,}")
            with col3:
                st.metric("Total Likes", f"{channel_data['Like_count'].sum():,}")
            
            # Create sub-tabs for different views
            subtab1, subtab2 = st.tabs(["Recent Videos", "Channel Statistics"])
            
            with subtab1:
                st.dataframe(
                    channel_data[['Published_date_ist', 'Title', 'View_count', 'Like_count']]
                    .sort_values('Published_date_ist', ascending=False),
                    use_container_width=True
                )
            
            with subtab2:
                st.subheader(f"Statistics for {channel}")
                # Calculate best performing video
                if not channel_data.empty:
                    best_video_idx = channel_data['View_count'].idxmax()
                    best_video = channel_data.loc[best_video_idx, 'Title']
                    
                    # Create statistics DataFrame
                    stats_df = pd.DataFrame({
                        'Metric': [
                            'Average Views',
                            'Maximum Views',
                            'Average Likes',
                            'Maximum Likes',
                            'Average Like/View Ratio',
                            'Best Performing Video (Views)'
                        ],
                        'Value': [
                            f"{channel_data['View_count'].mean():,.0f}",
                            f"{channel_data['View_count'].max():,}",
                            f"{channel_data['Like_count'].mean():,.0f}",
                            f"{channel_data['Like_count'].max():,}",
                            f"{(channel_data['Like_count'].sum() / channel_data['View_count'].sum() * 100):.2f}%",
                            best_video
                        ]
                    })
                    st.dataframe(stats_df, use_container_width=True)
                else:
                    st.write("No data available for this channel with the current filters.")
else:
    st.warning("Please select at least one channel to view analysis.")

# Overall Summary Table
st.header("Overall Performance Summary")
if not df_filtered.empty:
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
else:
    st.warning("No data available to generate summary statistics.")

# Download button for filtered data
st.header("Export Data")
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

if not df_filtered.empty:
    csv = convert_df_to_csv(df_filtered)
    st.download_button(
        "Download Filtered Data as CSV",
        csv,
        "youtube_analytics.csv",
        "text/csv",
        key='download-csv'
    )
else:
    st.warning("No data available to export.")