import panel as pn
import holoviews as hv
import pandas as pd
import numpy as np
from datetime import datetime
import sys
from bokeh.models import HoverTool
from holoviews import opts

# Initialize extensions
hv.extension('bokeh')
pn.extension()

# Load and preprocess data with improved error handling
def load_and_preprocess_data(file_path):
    try:
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        df = None
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                print(f"Successfully loaded file with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            print("Could not read the file with any of the attempted encodings")
            return pd.DataFrame()

        print("Available columns:", df.columns.tolist())

        if 'Published_date_ist' in df.columns:
            df['Published_date_ist'] = pd.to_datetime(df['Published_date_ist'])
        else:
            print("Warning: Missing Published_date_ist column")
            return pd.DataFrame()

        numeric_columns = ['View_count', 'Like_count', 'Comment_count']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                print(f"Warning: Missing {col} column")
                return pd.DataFrame()

        df = df.sort_values('Published_date_ist')
        df = df.dropna(subset=['Channel_title', 'Published_date_ist'] + numeric_columns)

        return df

    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return pd.DataFrame()

pn.extension()

# Load the data
print("Loading data...")
df = load_and_preprocess_data("./combined.csv")

if df.empty:
    print("Error: Could not load data properly. Please check the file and column names.")
    sys.exit(1)

# Generate unique colors for each channel
unique_channels = df["Channel_title"].unique().tolist()
channel_colors = {channel: hv.Cycle('Category10').values[i % 10] for i, channel in enumerate(unique_channels)}

# Widgets
channel_selector = pn.widgets.Select(
    name="Select Channel",
    options=['All Channels'] + sorted(df["Channel_title"].unique().tolist()),
    value='All Channels',
    width=400
)

date_range_slider = pn.widgets.DateRangeSlider(
    name='Date Range',
    start=df['Published_date_ist'].min(),
    end=df['Published_date_ist'].max(),
    value=(df['Published_date_ist'].min(), df['Published_date_ist'].max()),
    width=400
)

# Function to filter data
def filter_data(df, channel, date_range):
    date_mask = (df["Published_date_ist"] >= date_range[0]) & (df["Published_date_ist"] <= date_range[1])
    return df[date_mask] if channel == 'All Channels' else df[date_mask & (df["Channel_title"] == channel)]

# Function to create time series plots with channel-specific colors
def create_time_series(df, channel, date_range):
    filtered_df = filter_data(df, channel, date_range)

    hover = HoverTool(
        tooltips=[
            ('Channel', '@Channel_title'),
            ('Date', '@{Published_date_ist}{%F}'),
            ('Title', '@Title'),
            ('Views', '@{View_count}{0,}'),
            ('Likes', '@{Like_count}{0,}')
        ],
        formatters={'@Published_date_ist': 'datetime'}
    )

    plots = []
    grouped = filtered_df.groupby("Channel_title") if channel == 'All Channels' else {channel: filtered_df}

    for ch, ch_data in grouped:
        color = channel_colors.get(ch, 'black')  # Default to black if not found
        views_plot = hv.Curve(ch_data, kdims=['Published_date_ist'], vdims=['View_count']).opts(
            width=500, height=300, title='Video Views Trend', xlabel='Date', ylabel='Views',
            color=color, line_width=2, tools=['hover'], legend_position='right'
        )
        likes_plot = hv.Curve(ch_data, kdims=['Published_date_ist'], vdims=['Like_count']).opts(
            width=500, height=300, title='Video Likes Trend', xlabel='Date', ylabel='Likes',
            color=color, line_width=2, tools=['hover'], legend_position='right'
        )
        plots.append(views_plot)
        plots.append(likes_plot)

    return hv.Overlay(plots).opts(legend_position='right')

# Function to create video table
def create_video_table(df, channel, date_range):
    filtered_df = filter_data(df, channel, date_range)
    
    table_df = filtered_df[['Channel_title', 'Title', 'Published_date_ist', 'View_count', 'Like_count', 'Comment_count']].copy()
    table_df = table_df.sort_values('Published_date_ist', ascending=False)
    
    table_df['Published_date_ist'] = table_df['Published_date_ist'].dt.strftime('%Y-%m-%d')
    for col in ['View_count', 'Like_count', 'Comment_count']:
        table_df[col] = table_df[col].apply(lambda x: f"{x:,.0f}")
    
    return pn.widgets.DataFrame(table_df, width=1050, height=400)

# Function to get channel statistics
def get_channel_stats(df, channel, date_range):
    filtered_df = filter_data(df, channel, date_range)

    stats = pd.DataFrame({
        'Metric': ['Total Videos', 'Total Views', 'Average Views', 'Total Likes', 'Average Likes'],
        'Value': [
            len(filtered_df),
            f"{filtered_df['View_count'].sum():,.0f}",
            f"{filtered_df['View_count'].mean():,.0f}",
            f"{filtered_df['Like_count'].sum():,.0f}",
            f"{filtered_df['Like_count'].mean():,.0f}"
        ]
    })

    return pn.widgets.DataFrame(stats, width=1050)

# Dashboard function
@pn.depends(channel_selector.param.value, date_range_slider.param.value)
def create_dashboard(channel, date_range):
    try:
        time_series_plots = create_time_series(df, channel, date_range)
        stats_table = get_channel_stats(df, channel, date_range)
        video_table = create_video_table(df, channel, date_range)
        
        return pn.Column(
            pn.pane.Markdown("## Channel Statistics"),
            stats_table,
            pn.pane.Markdown("## Performance Trends"),
            time_series_plots,
            pn.pane.Markdown("## Video Details"),
            video_table
        )
    except Exception as e:
        return pn.Column(f"Error creating dashboard: {str(e)}")

# Final dashboard layout
dashboard = pn.Column(
    pn.pane.Markdown("# YouTube Channel Analytics Dashboard"),
    pn.Row(channel_selector, date_range_slider),
    create_dashboard
)

# Serve the dashboard
dashboard.servable()
