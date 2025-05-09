import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import pyngrok.ngrok as ngrok
import os

# Set page configuration
st.set_page_config(layout="wide", page_title="YouTube Analytics Dashboard")

# MySQL Database Configuration
hostname = "database-2.c9asogtdnypd.ap-south-1.rds.amazonaws.com"
dbname = "youtube_db4"
uname = "admin"
pwd = "SocialMkt22"

# Ngrok setup function
def setup_ngrok():
    # Get ngrok auth token from environment variable or use a default one for testing
    # You would need to set this with your actual ngrok token
    ngrok_auth_token = os.environ.get("NGROK_AUTH_TOKEN", "")
    
    if ngrok_auth_token:
        ngrok.set_auth_token(ngrok_auth_token)
    
    # Start ngrok tunnel to the streamlit port (default is 8501)
    ngrok_tunnel = ngrok.connect(addr="8501", proto="http", bind_tls=True)
    
    # Display the public URL
    ngrok_url = ngrok_tunnel.public_url
    st.sidebar.markdown(f"**Ngrok URL:** {ngrok_url}")
    
    return ngrok_url

# Create a connection to the database
def get_db_connection():
    try:
        engine = create_engine(f"mysql+pymysql://{uname}:{pwd}@{hostname}/{dbname}?charset=utf8")
        return engine
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

# Load data from MySQL
@st.cache_data
def load_data():
    engine = get_db_connection()
    if engine is None:
        # Return empty dataframe with expected columns if connection fails
        return pd.DataFrame(columns=['Published_date_ist', 'Channel_title', 'Type', 'View_count', 'Like_count', 'Title'])
    
    try:
        query = "SELECT * FROM Daliy_vod_inc LIMIT 100000"
        df = pd.read_sql(query, engine)
        
        # Convert date and ensure numeric columns
        df['Published_date_ist'] = pd.to_datetime(df['Published_date_ist'], errors='coerce')
        df['View_count'] = pd.to_numeric(df['View_count'], errors='coerce')
        df['Like_count'] = pd.to_numeric(df['Like_count'], errors='coerce')
        
        # Handle missing values
        df['View_count'].fillna(0, inplace=True)
        df['Like_count'].fillna(0, inplace=True)
        
        # Add month-year column for monthly analysis
        df['Month_Year'] = df['Published_date_ist'].dt.to_period('M').dt.to_timestamp()
        
        return df
    except Exception as e:
        st.error(f"Data loading error: {e}")
        # Return empty dataframe with expected columns
        return pd.DataFrame(columns=['Published_date_ist', 'Channel_title', 'Type', 'View_count', 'Like_count', 'Title'])

# Check if we're running in the Streamlit environment
if 'STREAMLIT_SHARING' not in os.environ:
    # Setup ngrok when running locally
    try:
        ngrok_url = setup_ngrok()
    except Exception as e:
        st.sidebar.error(f"Ngrok setup error: {e}")
        st.sidebar.warning("Install ngrok and pyngrok: pip install pyngrok")
        st.sidebar.info("To use ngrok, you need an auth token from ngrok.com")

# Main application code
try:
    # Load and prepare data
    df = load_data()

    # Sidebar Filters
    st.sidebar.header("Filters")

    # Only proceed with filtering if we have data
    if not df.empty:
        # Date Range Filter
        min_date = df['Published_date_ist'].min()
        max_date = df['Published_date_ist'].max()
        
        st.sidebar.subheader("Date Range Filter")
        date_range = st.sidebar.date_input(
            "Select Date Range",
            [min_date, max_date]
        )

        # Channel Filter
        st.sidebar.subheader("Channel Filter")
        channel_options = df['Channel_title'].unique()
        selected_channel = st.sidebar.multiselect(
            "Select Channel(s)",
            channel_options,
            default=channel_options[:5] if len(channel_options) > 5 else channel_options  # Default to first 5 channels
        )

        # Type Filter
        st.sidebar.subheader("Video Type Filter")
        type_options = df['Type'].unique()
        selected_types = st.sidebar.multiselect(
            "Select Video Type(s)",
            type_options,
            default=type_options
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
            (df['Type'].isin(selected_types)) &
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

        # Create tabs for daily and monthly views
        time_tab1, time_tab2 = st.tabs(["Daily Analysis", "Monthly Analysis"])

        with time_tab1:
            # Views Over Time (Daily)
            st.subheader("Views Over Time by Channel (Daily)")
            if not df_filtered.empty:
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
            else:
                st.info("No data available for the selected filters.")

            # Likes Over Time (Daily)
            st.subheader("Likes Over Time by Channel (Daily)")
            if not df_filtered.empty:
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
            else:
                st.info("No data available for the selected filters.")

        with time_tab2:
            # Views Over Time (Monthly)
            st.subheader("Views Over Time by Channel (Monthly)")
            if not df_filtered.empty:
                monthly_views = df_filtered.groupby(['Month_Year', 'Channel_title'])['View_count'].sum().reset_index()
                fig_monthly_views = px.line(
                    monthly_views,
                    x='Month_Year',
                    y='View_count',
                    color='Channel_title',
                    title='Monthly Views by Channel',
                    labels={'Month_Year': 'Month', 'View_count': 'Views', 'Channel_title': 'Channel'}
                )
                fig_monthly_views.update_traces(mode='lines+markers')
                st.plotly_chart(fig_monthly_views, use_container_width=True)
            else:
                st.info("No data available for the selected filters.")

            # Likes Over Time (Monthly)
            st.subheader("Likes Over Time by Channel (Monthly)")
            if not df_filtered.empty:
                monthly_likes = df_filtered.groupby(['Month_Year', 'Channel_title'])['Like_count'].sum().reset_index()
                fig_monthly_likes = px.line(
                    monthly_likes,
                    x='Month_Year',
                    y='Like_count',
                    color='Channel_title',
                    title='Monthly Likes by Channel',
                    labels={'Month_Year': 'Month', 'Like_count': 'Likes', 'Channel_title': 'Channel'}
                )
                fig_monthly_likes.update_traces(mode='lines+markers')
                st.plotly_chart(fig_monthly_likes, use_container_width=True)
            else:
                st.info("No data available for the selected filters.")

        # Video Type Analysis (only if filtered data exists)
        if not df_filtered.empty:
            st.header("Video Type Analysis")
            type_tab1, type_tab2, type_tab3 = st.tabs(["Type Distribution", "Performance by Type", "Type Trends"])

            with type_tab1:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Pie chart of video types
                    type_dist = df_filtered['Type'].value_counts()
                    fig_type_pie = px.pie(
                        values=type_dist.values,
                        names=type_dist.index,
                        title='Distribution of Video Types'
                    )
                    st.plotly_chart(fig_type_pie, use_container_width=True)
                
                with col2:
                    # Bar chart of video types by channel
                    type_channel_dist = df_filtered.groupby(['Channel_title', 'Type']).size().reset_index(name='count')
                    fig_type_channel = px.bar(
                        type_channel_dist,
                        x='Channel_title',
                        y='count',
                        color='Type',
                        title='Video Types by Channel',
                        barmode='group'
                    )
                    st.plotly_chart(fig_type_channel, use_container_width=True)

            with type_tab2:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Average views by type
                    avg_views_type = df_filtered.groupby('Type')['View_count'].mean().reset_index()
                    fig_avg_views = px.bar(
                        avg_views_type,
                        x='Type',
                        y='View_count',
                        title='Average Views by Video Type',
                        color='Type'
                    )
                    st.plotly_chart(fig_avg_views, use_container_width=True)
                
                with col2:
                    # Average likes by type
                    avg_likes_type = df_filtered.groupby('Type')['Like_count'].mean().reset_index()
                    fig_avg_likes = px.bar(
                        avg_likes_type,
                        x='Type',
                        y='Like_count',
                        title='Average Likes by Video Type',
                        color='Type'
                    )
                    st.plotly_chart(fig_avg_likes, use_container_width=True)

            with type_tab3:
                # Monthly trends by type
                monthly_type_views = df_filtered.groupby(['Month_Year', 'Type'])['View_count'].sum().reset_index()
                fig_monthly_type = px.line(
                    monthly_type_views,
                    x='Month_Year',
                    y='View_count',
                    color='Type',
                    title='Monthly Views by Video Type',
                    labels={'Month_Year': 'Month', 'View_count': 'Views'}
                )
                st.plotly_chart(fig_monthly_type, use_container_width=True)
                
                # Monthly video count by type
                monthly_type_count = df_filtered.groupby(['Month_Year', 'Type']).size().reset_index(name='count')
                fig_monthly_count = px.line(
                    monthly_type_count,
                    x='Month_Year',
                    y='count',
                    color='Type',
                    title='Number of Videos Published by Type Over Time',
                    labels={'Month_Year': 'Month', 'count': 'Number of Videos'}
                )
                st.plotly_chart(fig_monthly_count, use_container_width=True)

            # Individual Channel Analysis
            if selected_channel:
                st.header("Channel-specific Analysis")

                # Create tabs for each channel
                channel_tabs = st.tabs(selected_channel)

                for i, tab in enumerate(channel_tabs):
                    channel = selected_channel[i]
                    with tab:
                        channel_data = df_filtered[df_filtered['Channel_title'] == channel]
                        
                        if not channel_data.empty:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Videos", len(channel_data))
                            with col2:
                                st.metric("Total Views", f"{channel_data['View_count'].sum():,}")
                            with col3:
                                st.metric("Total Likes", f"{channel_data['Like_count'].sum():,}")
                            
                            # Create sub-tabs for different views
                            subtab1, subtab2, subtab3, subtab4 = st.tabs(["Recent Videos", "Channel Statistics", "Monthly Breakdown", "Performance Graphs"])
                            
                            with subtab1:
                                st.dataframe(
                                    channel_data[['Published_date_ist', 'Title', 'View_count', 'Like_count']]
                                    .sort_values('Published_date_ist', ascending=False),
                                    use_container_width=True
                                )
                            
                            with subtab2:
                                st.subheader(f"Statistics for {channel}")
                                best_video_idx = channel_data['View_count'].idxmax()
                                best_video = channel_data.loc[best_video_idx, 'Title']
                                
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
                                        f"{(channel_data['Like_count'].sum() / channel_data['View_count'].sum() * 100 if channel_data['View_count'].sum() > 0 else 0):.2f}%",
                                        best_video
                                    ]
                                })
                                st.dataframe(stats_df, use_container_width=True)
                            
                            with subtab3:
                                st.subheader(f"Monthly Performance for {channel}")
                                monthly_channel_data = channel_data.groupby('Month_Year').agg({
                                    'View_count': ['sum', 'mean'],
                                    'Like_count': ['sum', 'mean'],
                                    'Title': 'count'
                                }).reset_index()
                                
                                monthly_channel_data.columns = ['Month', 'Total Views', 'Avg Views', 'Total Likes', 'Avg Likes', 'Videos Published']
                                st.dataframe(monthly_channel_data.sort_values('Month', ascending=False), use_container_width=True)
                            
                            with subtab4:
                                st.subheader(f"Performance Graphs for {channel}")
                                
                                # Daily graphs subtabs
                                graph_tab1, graph_tab2 = st.tabs(["Daily Performance", "Monthly Performance"])
                                
                                with graph_tab1:
                                    # Views Over Time (Daily)
                                    st.subheader(f"Daily Views for {channel}")
                                    channel_daily_views = channel_data.groupby('Published_date_ist')['View_count'].sum().reset_index()
                                    fig_channel_daily_views = px.line(
                                        channel_daily_views,
                                        x='Published_date_ist',
                                        y='View_count',
                                        title=f'Daily Views for {channel}',
                                        labels={'Published_date_ist': 'Date', 'View_count': 'Views'}
                                    )
                                    fig_channel_daily_views.update_traces(mode='lines+markers')
                                    st.plotly_chart(fig_channel_daily_views, use_container_width=True)
                                    
                                    # Likes Over Time (Daily)
                                    st.subheader(f"Daily Likes for {channel}")
                                    channel_daily_likes = channel_data.groupby('Published_date_ist')['Like_count'].sum().reset_index()
                                    fig_channel_daily_likes = px.line(
                                        channel_daily_likes,
                                        x='Published_date_ist',
                                        y='Like_count',
                                        title=f'Daily Likes for {channel}',
                                        labels={'Published_date_ist': 'Date', 'Like_count': 'Likes'}
                                    )
                                    fig_channel_daily_likes.update_traces(mode='lines+markers')
                                    st.plotly_chart(fig_channel_daily_likes, use_container_width=True)
                                
                                with graph_tab2:
                                    # Monthly views
                                    st.subheader(f"Monthly Views for {channel}")
                                    channel_monthly_views = channel_data.groupby('Month_Year')['View_count'].sum().reset_index()
                                    fig_channel_monthly_views = px.line(
                                        channel_monthly_views,
                                        x='Month_Year',
                                        y='View_count',
                                        title=f'Monthly Views for {channel}',
                                        labels={'Month_Year': 'Month', 'View_count': 'Views'}
                                    )
                                    fig_channel_monthly_views.update_traces(mode='lines+markers')
                                    st.plotly_chart(fig_channel_monthly_views, use_container_width=True)
                                    
                                    # Monthly likes
                                    st.subheader(f"Monthly Likes for {channel}")
                                    channel_monthly_likes = channel_data.groupby('Month_Year')['Like_count'].sum().reset_index()
                                    fig_channel_monthly_likes = px.line(
                                        channel_monthly_likes,
                                        x='Month_Year',
                                        y='Like_count',
                                        title=f'Monthly Likes for {channel}',
                                        labels={'Month_Year': 'Month', 'Like_count': 'Likes'}
                                    )
                                    fig_channel_monthly_likes.update_traces(mode='lines+markers')
                                    st.plotly_chart(fig_channel_monthly_likes, use_container_width=True)
                        else:
                            st.info(f"No data available for {channel} with the current filters.")

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
                st.info("No data available for the selected filters.")

            # Monthly Summary Table
            st.header("Monthly Performance Summary")
            if not df_filtered.empty:
                monthly_summary = df_filtered.groupby(['Month_Year']).agg({
                    'View_count': ['sum', 'mean'],
                    'Like_count': ['sum', 'mean'],
                    'Title': 'count'
                }).round(2)

                monthly_summary.columns = [
                    'Total Views', 'Avg Views Per Video',
                    'Total Likes', 'Avg Likes Per Video',
                    'Videos Published'
                ]
                monthly_summary = monthly_summary.reset_index()
                st.dataframe(monthly_summary.sort_values('Month_Year', ascending=False), use_container_width=True)
            else:
                st.info("No data available for the selected filters.")

            # Type Summary Table
            st.header("Video Type Summary")
            if not df_filtered.empty:
                type_summary = df_filtered.groupby('Type').agg({
                    'View_count': ['count', 'sum', 'mean', 'max'],
                    'Like_count': ['sum', 'mean', 'max']
                }).round(2)

                type_summary.columns = [
                    'Total Videos', 'Total Views', 'Avg Views', 'Max Views',
                    'Total Likes', 'Avg Likes', 'Max Likes'
                ]
                type_summary = type_summary.reset_index()
                st.dataframe(type_summary, use_container_width=True)
            else:
                st.info("No data available for the selected filters.")

            # Download buttons
            st.header("Export Data")

            @st.cache_data
            def convert_df_to_csv(df):
                return df.to_csv(index=False).encode('utf-8')

            # Download filtered data
            csv = convert_df_to_csv(df_filtered)
            st.download_button(
                "Download Filtered Data as CSV",
                csv,
                "youtube_analytics.csv",
                "text/csv",
                key='download-csv'
            )

            # Download monthly summary
            if 'monthly_summary' in locals() and not monthly_summary.empty:
                monthly_csv = convert_df_to_csv(monthly_summary)
                st.download_button(
                    "Download Monthly Summary as CSV",
                    monthly_csv,
                    "youtube_monthly_summary.csv",
                    "text/csv",
                    key='download-monthly-csv'
                )

            # Download type summary
            if 'type_summary' in locals() and not type_summary.empty:
                type_summary_csv = convert_df_to_csv(type_summary)
                st.download_button(
                    "Download Type Summary as CSV",
                    type_summary_csv,
                    "youtube_type_summary.csv",
                    "text/csv",
                    key='download-type-csv'
                )
    else:
        st.error("No data available. Please check your database connection.")

except Exception as e:
    st.error(f"An error occurred: {e}")
    st.info("Please check your database connection and try again.")

# Add a footer
st.markdown("---")
st.markdown("YouTube Analytics Dashboard | Built with Streamlit and ngrok")