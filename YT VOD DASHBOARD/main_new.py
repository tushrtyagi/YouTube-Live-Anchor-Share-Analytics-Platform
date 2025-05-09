import panel as pn
import holoviews as hv
import pandas as pd
import numpy as np
from datetime import datetime

# Initialize extensions
hv.extension('bokeh')
pn.extension()

# Load and preprocess data
def load_and_preprocess_data(file_path):
    try:
        df = pd.read_csv(file_path)
        df['Published_date_ist'] = pd.to_datetime(df['Published_date_ist'])
        
        # Convert numeric columns to appropriate types
        numeric_columns = ['View_count', 'Like_count', 'Comment_count']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Sort by date
        df = df.sort_values('Published_date_ist')
        
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_and_preprocess_data("./combined.csv")

# Create widgets
channel_selector = pn.widgets.Select(
    name="Select Channel",
    options=sorted(df["Channel_title"].unique().tolist()),
    width=400
)

date_range_slider = pn.widgets.DateRangeSlider(
    name='Date Range',
    start=df['Published_date_ist'].min(),
    end=df['Published_date_ist'].max(),
    value=(df['Published_date_ist'].min(), df['Published_date_ist'].max()),
    width=400
)

# Function to create time series plots
def create_time_series(df, channel, date_range):
    # Filter data
    mask = (
        (df["Channel_title"] == channel) &
        (df["Published_date_ist"] >= date_range[0]) &
        (df["Published_date_ist"] <= date_range[1])
    )
    filtered_df = df[mask]
    
    # Aggregate daily metrics
    daily_metrics = filtered_df.groupby("Published_date_ist").agg({
        "View_count": "sum",
        "Like_count": "sum"
    }).reset_index()
    
    # Create views plot
    views_plot = hv.Curve(
        daily_metrics, 
        kdims=["Published_date_ist"], 
        vdims=["View_count"]
    ).opts(
        width=800,
        height=300,
        title=f'Daily Views for {channel}',
        xlabel='Date',
        ylabel='Total Views',
        tools=['hover'],
        line_width=2,
        color='navy'
    )
    
    # Create likes plot
    likes_plot = hv.Curve(
        daily_metrics, 
        kdims=["Published_date_ist"], 
        vdims=["Like_count"]
    ).opts(
        width=800,
        height=300,
        title=f'Daily Likes for {channel}',
        xlabel='Date',
        ylabel='Total Likes',
        tools=['hover'],
        line_width=2,
        color='darkred'
    )
    
    # Return both plots stacked vertically
    return (views_plot + likes_plot).cols(1)

# Function to update stats
def get_channel_stats(df, channel, date_range):
    mask = (
        (df["Channel_title"] == channel) &
        (df["Published_date_ist"] >= date_range[0]) &
        (df["Published_date_ist"] <= date_range[1])
    )
    filtered_df = df[mask]
    
    stats = pd.DataFrame({
        'Metric': ['Total Videos', 'Total Views', 'Average Views per Video', 
                  'Total Likes', 'Average Likes per Video',
                  'Total Comments', 'Average Comments per Video'],
        'Value': [
            len(filtered_df),
            filtered_df['View_count'].sum(),
            filtered_df['View_count'].mean(),
            filtered_df['Like_count'].sum(),
            filtered_df['Like_count'].mean(),
            filtered_df['Comment_count'].sum(),
            filtered_df['Comment_count'].mean()
        ]
    })
    
    # Format numbers
    stats['Value'] = stats['Value'].apply(lambda x: f"{x:,.0f}")
    
    return pn.widgets.DataFrame(stats, width=400)

# Function to create video table
def create_video_table(df, channel, date_range):
    mask = (
        (df["Channel_title"] == channel) &
        (df["Published_date_ist"] >= date_range[0]) &
        (df["Published_date_ist"] <= date_range[1])
    )
    filtered_df = df[mask]
    
    table_df = filtered_df[['Title', 'Published_date_ist', 'View_count', 
                           'Like_count', 'Comment_count']].copy()
    
    # Format the columns
    table_df['Published_date_ist'] = table_df['Published_date_ist'].dt.strftime('%Y-%m-%d')
    table_df['View_count'] = table_df['View_count'].apply(lambda x: f"{x:,.0f}")
    table_df['Like_count'] = table_df['Like_count'].apply(lambda x: f"{x:,.0f}")
    table_df['Comment_count'] = table_df['Comment_count'].apply(lambda x: f"{x:,.0f}")
    
    return pn.widgets.DataFrame(table_df, width=800)

# Create interactive dashboard
@pn.depends(channel_selector.param.value, date_range_slider.param.value)
def create_dashboard(channel, date_range):
    if not channel:
        return pn.Column("Please select a channel")
    
    # Create components
    time_series_plots = create_time_series(df, channel, date_range)
    stats_table = get_channel_stats(df, channel, date_range)
    video_table = create_video_table(df, channel, date_range)
    
    # Layout
    return pn.Column(
        pn.Row(
            pn.Column(
                "## Channel Statistics",
                stats_table
            ),
            pn.Column(
                "## Channel Metrics Over Time",
                time_series_plots
            )
        ),
        pn.Column(
            "## Video Details",
            video_table
        )
    )

# Final dashboard layout
dashboard = pn.Column(
    "# YouTube Channel Analytics Dashboard",
    pn.Row(
        channel_selector,
        date_range_slider
    ),
    create_dashboard
)

# Serve the dashboard
dashboard.servable()