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
        
        numeric_columns = ['View_count', 'Like_count', 'Comment_count']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.sort_values('Published_date_ist')
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_and_preprocess_data("./vod_data_all.csv")

# Custom CSS for styling
custom_css = """
.bk-root {
    background-color: #f5f8fa;
}
.dashboard-container {
    padding: 20px;
    min-width:100vw;
    background-color: #f5f8fa;
    min-height: 100vh;
}
.stats-card {
    background-color: white;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.chart-container {
    background-color: white;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
.table-container {
    background-color: white;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
"""

pn.extension(raw_css=[custom_css])

# Create styled widgets
channel_selector = pn.widgets.Select(
    name="Select Channel",
    options=['All'] + sorted(df["Channel_title"].unique().tolist()),
    value='All',
    width=400,
    styles={'background': 'white', 'font-size': '14px'}
)

date_range_slider = pn.widgets.DateRangeSlider(
    name='Date Range',
    start=df['Published_date_ist'].min(),
    end=df['Published_date_ist'].max(),
    value=(df['Published_date_ist'].min(), df['Published_date_ist'].max()),
    width=400,
    styles={'background': 'white'}
)

# Function to filter data based on channel and date range
def filter_data(df, channel, date_range):
    if channel == 'All':
        mask = (
            (df["Published_date_ist"] >= date_range[0]) &
            (df["Published_date_ist"] <= date_range[1])
        )
    else:
        mask = (
            (df["Channel_title"] == channel) &
            (df["Published_date_ist"] >= date_range[0]) &
            (df["Published_date_ist"] <= date_range[1])
        )
    return df[mask]

# Function to create time series plots
def create_time_series(df, channel, date_range):
    filtered_df = filter_data(df, channel, date_range)
    
    daily_metrics = filtered_df.groupby("Published_date_ist").agg({
        "View_count": "sum",
        "Like_count": "sum"
    }).reset_index()
    
    # Create views plot with improved styling
    views_plot = hv.Curve(
        daily_metrics, 
        kdims=["Published_date_ist"], 
        vdims=["View_count"]
    ).opts(
        width=500,
        height=300,
        title=f'Daily Views for {channel}',
        xlabel='Date',
        ylabel='Total Views',
        tools=['hover'],
        line_width=2,
        color='#1f77b4',
        bgcolor='white'
    )
    
    # Create likes plot with improved styling
    likes_plot = hv.Curve(
        daily_metrics, 
        kdims=["Published_date_ist"], 
        vdims=["Like_count"]
    ).opts(
        width=500,
        height=300,
        title=f'Daily Likes for {channel}',
        xlabel='Date',
        ylabel='Total Likes',
        tools=['hover'],
        line_width=2,
        color='#d62728',
        bgcolor='white'
    )
    
    return (views_plot + likes_plot).cols(2)

def get_channel_stats(df, channel, date_range):
    filtered_df = filter_data(df, channel, date_range)
    
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
    
    stats['Value'] = stats['Value'].apply(lambda x: f"{x:,.0f}")
    
    return pn.widgets.DataFrame(
        stats, 
        width=400,
        styles={
            'background': 'white',
            'font-family': 'Arial',
            'font-size': '12px'
        }
    )

def create_video_table(df, channel, date_range):
    filtered_df = filter_data(df, channel, date_range)
    
    table_df = filtered_df[['Channel_title', 'Title', 'Published_date_ist', 'View_count', 
                           'Like_count', 'Comment_count']].copy()
    
    table_df['Published_date_ist'] = table_df['Published_date_ist'].dt.strftime('%Y-%m-%d')
    table_df['View_count'] = table_df['View_count'].apply(lambda x: f"{x:,.0f}")
    table_df['Like_count'] = table_df['Like_count'].apply(lambda x: f"{x:,.0f}")
    table_df['Comment_count'] = table_df['Comment_count'].apply(lambda x: f"{x:,.0f}")
    
    return pn.widgets.DataFrame(
        table_df, 
        width=1050,
        styles={
            'background': 'white',
            'font-family': 'Arial',
            'font-size': '12px'
        }
    )

# Create interactive dashboard with improved styling
@pn.depends(channel_selector.param.value, date_range_slider.param.value)
def create_dashboard(channel, date_range):
    if not channel:
        return pn.Column("Please select a channel")
    
    time_series_plots = create_time_series(df, channel, date_range)
    stats_table = get_channel_stats(df, channel, date_range)
    video_table = create_video_table(df, channel, date_range)
    
    return pn.Column(
        pn.Row(
            pn.Column(
                pn.pane.Markdown("## Channel Statistics", styles={'color': '#2c3e50'}),
                stats_table,
                css_classes=['stats-card']
            ),
        ),
        pn.Column(
            pn.pane.Markdown("## Channel Metrics Over Time", styles={'color': '#2c3e50'}),
            time_series_plots,
            css_classes=['chart-container']
        ),
        pn.Column(
            pn.pane.Markdown("## Video Details", styles={'color': '#2c3e50'}),
            video_table,
            css_classes=['table-container']
        ),
        css_classes=['dashboard-container']
    )

# Final dashboard layout with styling
dashboard = pn.Column(
    pn.pane.Markdown("# YouTube Channel Analytics Dashboard", styles={
        'color': '#2c3e50',
        'font-family': 'Arial',
        'font-size': '32px',
        'font-weight': 'bold',
        'text-align': 'center',
        'margin': '20px 0'
    }),
    pn.Row(
        channel_selector,
        date_range_slider,
        styles={'background': '#f5f8fa', 'padding': '20px'}
    ),
    create_dashboard,
    styles={'background': '#f5f8fa'}
)

# Serve the dashboard
dashboard.servable()