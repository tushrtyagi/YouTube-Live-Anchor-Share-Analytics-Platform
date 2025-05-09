import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Set page configuration
st.set_page_config(layout="wide")

# Load data from Excel files
@st.cache_data
def load_data():
    # Paths to both Excel files
    file_path1 = r"C:\Users\admin\Downloads\combined_dff_Oct24_Jan25 (1) (1).xlsx"
    file_path2 = r"C:\Users\admin\Downloads\combined_dff_Jul24_Sep24 (1) (1).xlsx"
    
    # Read both files
    df1 = pd.read_excel(file_path1)
    df2 = pd.read_excel(file_path2)
    
    # Combine the dataframes
    df = pd.concat([df1, df2], ignore_index=True)
    
    # Remove duplicates if any (based on video ID or other unique identifier if available)
    if 'Video_id' in df.columns:
        df = df.drop_duplicates(subset=['Video_id'])
    
    # Ensure date column is datetime
    df['Published_date_ist'] = pd.to_datetime(df['Published_date_ist'], errors='coerce')
    
    # Ensure numeric conversion for View_count and Like_count
    df['View_count'] = pd.to_numeric(df['View_count'], errors='coerce')
    df['Like_count'] = pd.to_numeric(df['Like_count'], errors='coerce')
    df['View_count'].fillna(0, inplace=True)
    df['Like_count'].fillna(0, inplace=True)
    
    # Add month-year column for monthly analysis
    df['Month_Year'] = df['Published_date_ist'].dt.to_period('M').dt.to_timestamp()
    
    return df

# Load channel categories from CSV
@st.cache_data
def load_channel_categories():
    # Load the channel categories CSV
    channel_csv_path = "CHANNEL_LIST.csv"  # Update path if needed
    if os.path.exists(channel_csv_path):
        # Read the CSV file
        categories_df = pd.read_csv(channel_csv_path)
        
        # Create a dictionary to store channels by category
        categories = {}
        for column in categories_df.columns:
            # Filter out NaN values and create a list of channels for this category
            channels = categories_df[column].dropna().tolist()
            categories[column.strip()] = channels
        
        return categories
    else:
        # If CSV file doesn't exist, return empty dictionary
        st.warning(f"Channel categories file not found at {channel_csv_path}")
        return {}

# Load and prepare data
try:
    df = load_data()
    channel_categories = load_channel_categories()
    data_loaded = True
except Exception as e:
    st.error(f"Error loading data: {e}")
    data_loaded = False

if data_loaded:
    # Create a mapping from channel to category
    channel_to_category = {}
    for category, channels in channel_categories.items():
        for channel in channels:
            channel_to_category[channel.strip()] = category.strip()
    
    # Add a Category column to the dataframe
    df['Category'] = df['Channel_title'].map(channel_to_category)
    
    # For channels not in our mapping, set category as "Other"
    df['Category'].fillna("Other", inplace=True)
    
    # Sidebar Filters
    st.sidebar.header("Filters")

    # Date Range Filter
    st.sidebar.subheader("Date Range Filter")
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [df['Published_date_ist'].min(), df['Published_date_ist'].max()]
    )

    # Category Filter
    st.sidebar.subheader("Category Filter")
    available_categories = sorted(df['Category'].unique())
    selected_categories = st.sidebar.multiselect(
        "Select Categories",
        available_categories,
        default=available_categories
    )

    # Channel Filter
    st.sidebar.subheader("Channel Filter")
    # Only show channels from selected categories
    filtered_channel_options = df[df['Category'].isin(selected_categories)]['Channel_title'].unique()
    selected_channel = st.sidebar.multiselect(
        "Select Channel(s)",
        filtered_channel_options,
        default=filtered_channel_options
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
    st.caption("Data range: July 2024 - January 2025")

    # Overview Metrics
    st.header("Overview Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Videos", len(df_filtered))
    with col2:
        st.metric("Total Views", f"{df_filtered['View_count'].sum():,}")
    with col3:
        st.metric("Total Likes", f"{df_filtered['Like_count'].sum():,}")
    with col4:
        st.metric("Categories", len(df_filtered['Category'].unique()))

    # Time series visualizations
    st.header("Time Series Analysis")

    # Create tabs for daily and monthly views
    time_tab1, time_tab2 = st.tabs(["Daily Analysis", "Monthly Analysis"])

    with time_tab1:
        # Views Over Time (Daily)
        st.subheader("Views Over Time by Category (Daily)")
        daily_views = df_filtered.groupby(['Published_date_ist', 'Category'])['View_count'].sum().reset_index()
        fig_views = px.line(
            daily_views,
            x='Published_date_ist',
            y='View_count',
            color='Category',
            title='Daily Views by Category',
            labels={'Published_date_ist': 'Date', 'View_count': 'Views', 'Category': 'Category'}
        )
        fig_views.update_traces(mode='lines+markers')
        st.plotly_chart(fig_views, use_container_width=True)

        # Likes Over Time (Daily)
        st.subheader("Likes Over Time by Category (Daily)")
        daily_likes = df_filtered.groupby(['Published_date_ist', 'Category'])['Like_count'].sum().reset_index()
        fig_likes = px.line(
            daily_likes,
            x='Published_date_ist',
            y='Like_count',
            color='Category',
            title='Daily Likes by Category',
            labels={'Published_date_ist': 'Date', 'Like_count': 'Likes', 'Category': 'Category'}
        )
        fig_likes.update_traces(mode='lines+markers')
        st.plotly_chart(fig_likes, use_container_width=True)

    with time_tab2:
        # Views Over Time (Monthly)
        st.subheader("Views Over Time by Category (Monthly)")
        monthly_views = df_filtered.groupby(['Month_Year', 'Category'])['View_count'].sum().reset_index()
        fig_monthly_views = px.line(
            monthly_views,
            x='Month_Year',
            y='View_count',
            color='Category',
            title='Monthly Views by Category',
            labels={'Month_Year': 'Month', 'View_count': 'Views', 'Category': 'Category'}
        )
        fig_monthly_views.update_traces(mode='lines+markers')
        st.plotly_chart(fig_monthly_views, use_container_width=True)

        # Likes Over Time (Monthly)
        st.subheader("Likes Over Time by Category (Monthly)")
        monthly_likes = df_filtered.groupby(['Month_Year', 'Category'])['Like_count'].sum().reset_index()
        fig_monthly_likes = px.line(
            monthly_likes,
            x='Month_Year',
            y='Like_count',
            color='Category',
            title='Monthly Likes by Category',
            labels={'Month_Year': 'Month', 'Like_count': 'Likes', 'Category': 'Category'}
        )
        fig_monthly_likes.update_traces(mode='lines+markers')
        st.plotly_chart(fig_monthly_likes, use_container_width=True)

    # Category-wise Analysis
    st.header("Category-wise Analysis")
    
    # Create tabs for each category
    category_tabs = st.tabs(sorted(df_filtered['Category'].unique()))
    
    for i, tab in enumerate(category_tabs):
        category = sorted(df_filtered['Category'].unique())[i]
        
        with tab:
            category_data = df_filtered[df_filtered['Category'] == category]
            
            # Category Overview Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Channels", category_data['Channel_title'].nunique())
            with col2:
                st.metric("Total Videos", len(category_data))
            with col3:
                st.metric("Total Views", f"{category_data['View_count'].sum():,}")
            with col4:
                st.metric("Total Likes", f"{category_data['Like_count'].sum():,}")
            
            # Channel selector for this category
            channels_in_category = sorted(category_data['Channel_title'].unique())
            selected_channels_in_category = st.multiselect(
                f"Select {category} Channels to Compare",
                channels_in_category,
                default=channels_in_category[:min(5, len(channels_in_category))]
            )
            
            # Filter data for selected channels in this category
            if selected_channels_in_category:
                selected_category_data = category_data[category_data['Channel_title'].isin(selected_channels_in_category)]
                
                # Monthly performance comparison
                st.subheader(f"Monthly Views Comparison for Selected {category} Channels")
                monthly_channel_views = selected_category_data.groupby(['Month_Year', 'Channel_title'])['View_count'].sum().reset_index()
                fig_monthly_channel_views = px.line(
                    monthly_channel_views,
                    x='Month_Year',
                    y='View_count',
                    color='Channel_title',
                    title=f'Monthly Views by Channel in {category} Category',
                    labels={'Month_Year': 'Month', 'View_count': 'Views', 'Channel_title': 'Channel'}
                )
                fig_monthly_channel_views.update_traces(mode='lines+markers')
                st.plotly_chart(fig_monthly_channel_views, use_container_width=True)
                
                # Channel comparison table
                st.subheader(f"Channel Comparison in {category} Category")
                channel_comparison = selected_category_data.groupby('Channel_title').agg({
                    'View_count': ['count', 'sum', 'mean'],
                    'Like_count': ['sum', 'mean']
                }).round(2)
                
                channel_comparison.columns = [
                    'Total Videos', 'Total Views', 'Avg Views',
                    'Total Likes', 'Avg Likes'
                ]
                
                # Calculate engagement rate (likes/views)
                channel_totals = selected_category_data.groupby('Channel_title').agg({
                    'View_count': 'sum',
                    'Like_count': 'sum'
                })
                channel_totals['Engagement Rate'] = (channel_totals['Like_count'] / channel_totals['View_count'] * 100).round(2)
                
                # Merge with comparison table
                channel_comparison = channel_comparison.reset_index()
                channel_comparison['Engagement Rate'] = channel_totals['Engagement Rate'].values
                
                st.dataframe(channel_comparison, use_container_width=True)
                
                # Display individual channel tabs
                st.subheader(f"Individual Channel Analysis in {category} Category")
                channel_subtabs = st.tabs(selected_channels_in_category)
                
                for j, channel_tab in enumerate(channel_subtabs):
                    channel = selected_channels_in_category[j]
                    
                    with channel_tab:
                        channel_specific_data = selected_category_data[selected_category_data['Channel_title'] == channel]
                        
                        # Channel metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Videos", len(channel_specific_data))
                        with col2:
                            st.metric("Total Views", f"{channel_specific_data['View_count'].sum():,}")
                        with col3:
                            st.metric("Total Likes", f"{channel_specific_data['Like_count'].sum():,}")
                        
                        # Create sub-tabs for different views
                        subtab1, subtab2, subtab3 = st.tabs(["Recent Videos", "Channel Statistics", "Performance Graphs"])
                        
                        with subtab1:
                            st.dataframe(
                                channel_specific_data[['Published_date_ist', 'Title', 'View_count', 'Like_count']]
                                .sort_values('Published_date_ist', ascending=False),
                                use_container_width=True
                            )
                        
                        with subtab2:
                            st.subheader(f"Statistics for {channel}")
                            # Calculate best performing video
                            if not channel_specific_data.empty:
                                best_video_idx = channel_specific_data['View_count'].idxmax()
                                best_video = channel_specific_data.loc[best_video_idx, 'Title']
                                
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
                                        f"{channel_specific_data['View_count'].mean():,.0f}",
                                        f"{channel_specific_data['View_count'].max():,}",
                                        f"{channel_specific_data['Like_count'].mean():,.0f}",
                                        f"{channel_specific_data['Like_count'].max():,}",
                                        f"{(channel_specific_data['Like_count'].sum() / channel_specific_data['View_count'].sum() * 100):.2f}%",
                                        best_video
                                    ]
                                })
                                st.dataframe(stats_df, use_container_width=True)
                            else:
                                st.write("No data available for this channel with the current filters.")
                        
                        with subtab3:
                            # Monthly performance graphs
                            st.subheader(f"Monthly Performance for {channel}")
                            monthly_data = channel_specific_data.groupby('Month_Year').agg({
                                'View_count': 'sum',
                                'Like_count': 'sum',
                                'Title': 'count'
                            }).reset_index()
                            
                            monthly_data.columns = ['Month', 'Views', 'Likes', 'Videos']
                            
                            # Views graph
                            fig_views = px.line(
                                monthly_data,
                                x='Month',
                                y='Views',
                                title=f'Monthly Views for {channel}',
                                labels={'Month': 'Month', 'Views': 'Views'},
                                markers=True
                            )
                            st.plotly_chart(fig_views, use_container_width=True)
                            
                            # Likes graph
                            fig_likes = px.line(
                                monthly_data,
                                x='Month',
                                y='Likes',
                                title=f'Monthly Likes for {channel}',
                                labels={'Month': 'Month', 'Likes': 'Likes'},
                                markers=True
                            )
                            st.plotly_chart(fig_likes, use_container_width=True)
            else:
                st.warning(f"Please select at least one {category} channel to view channel analysis.")

    # Individual Channel Analysis
    st.header("Individual Channel Analysis")
    
    if selected_channel:
        # Create tabs for each channel
        channel_tabs = st.tabs(selected_channel)
        
        for i, tab in enumerate(channel_tabs):
            channel = selected_channel[i]
            with tab:
                channel_data = df_filtered[df_filtered['Channel_title'] == channel]
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Videos", len(channel_data))
                with col2:
                    st.metric("Total Views", f"{channel_data['View_count'].sum():,}")
                with col3:
                    st.metric("Total Likes", f"{channel_data['Like_count'].sum():,}")
                with col4:
                    category_name = channel_data['Category'].iloc[0] if not channel_data.empty else "Unknown"
                    st.metric("Category", category_name)
                
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
                
                with subtab3:
                    st.subheader(f"Monthly Performance for {channel}")
                    # Group channel data by month
                    monthly_channel_data = channel_data.groupby('Month_Year').agg({
                        'View_count': ['sum', 'mean'],
                        'Like_count': ['sum', 'mean'],
                        'Title': 'count'
                    }).reset_index()
                    
                    monthly_channel_data.columns = ['Month', 'Total Views', 'Avg Views', 'Total Likes', 'Avg Likes', 'Videos Published']
                    
                    # Display monthly breakdown
                    st.dataframe(monthly_channel_data.sort_values('Month', ascending=False), use_container_width=True)
                    
                    # Monthly trend charts
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_monthly_views_channel = px.line(
                            monthly_channel_data,
                            x='Month',
                            y='Total Views',
                            title=f'Monthly Views for {channel}',
                            markers=True
                        )
                        st.plotly_chart(fig_monthly_views_channel, use_container_width=True)
                    
                    with col2:
                        fig_monthly_likes_channel = px.line(
                            monthly_channel_data,
                            x='Month',
                            y='Total Likes',
                            title=f'Monthly Likes for {channel}',
                            markers=True
                        )
                        st.plotly_chart(fig_monthly_likes_channel, use_container_width=True)
                
                with subtab4:
                    st.subheader(f"Performance Graphs for {channel}")
                    
                    # Daily graphs subtabs
                    graph_tab1, graph_tab2 = st.tabs(["Daily Performance", "Monthly Performance"])
                    
                    with graph_tab1:
                        # Views Over Time (Daily) for this channel
                        st.subheader(f"Daily Views for {channel}")
                        channel_daily_views = channel_data.groupby('Published_date_ist')['View_count'].sum().reset_index()
                        fig_channel_daily_views = px.line(
                            channel_daily_views,
                            x='Published_date_ist',
                            y='View_count',
                            title=f'Daily Views for {channel}',
                            labels={'Published_date_ist': 'Date', 'View_count': 'Views'}
                        )
                        fig_channel_daily_views.update_traces(mode='lines+markers', line=dict(color='blue'))
                        st.plotly_chart(fig_channel_daily_views, use_container_width=True)
                        
                        # Likes Over Time (Daily) for this channel
                        st.subheader(f"Daily Likes for {channel}")
                        channel_daily_likes = channel_data.groupby('Published_date_ist')['Like_count'].sum().reset_index()
                        fig_channel_daily_likes = px.line(
                            channel_daily_likes,
                            x='Published_date_ist',
                            y='Like_count',
                            title=f'Daily Likes for {channel}',
                            labels={'Published_date_ist': 'Date', 'Like_count': 'Likes'}
                        )
                        fig_channel_daily_likes.update_traces(mode='lines+markers', line=dict(color='green'))
                        st.plotly_chart(fig_channel_daily_likes, use_container_width=True)
                        
                        # Combined views and likes (dual y-axis)
                        st.subheader(f"Combined Daily Metrics for {channel}")
                        fig_combined = px.line(
                            channel_daily_views,
                            x='Published_date_ist',
                            y='View_count',
                            title=f'Daily Views and Likes for {channel}',
                            labels={'Published_date_ist': 'Date', 'value': 'Count', 'variable': 'Metric'}
                        )
                        fig_combined.add_scatter(
                            x=channel_daily_likes['Published_date_ist'],
                            y=channel_daily_likes['Like_count'],
                            mode='lines+markers',
                            name='Likes',
                            yaxis='y2'
                        )
                        
                        # Update layout for dual y-axis
                        fig_combined.update_layout(
                            yaxis=dict(title='Views', titlefont=dict(color='blue'), tickfont=dict(color='blue')),
                            yaxis2=dict(
                                title='Likes',
                                titlefont=dict(color='green'),
                                tickfont=dict(color='green'),
                                anchor='x',
                                overlaying='y',
                                side='right'
                            ),
                            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
                        )
                        st.plotly_chart(fig_combined, use_container_width=True)
                    
                    with graph_tab2:
                        # Monthly views for this channel
                        st.subheader(f"Monthly Views for {channel}")
                        channel_monthly_views = channel_data.groupby('Month_Year')['View_count'].sum().reset_index()
                        fig_channel_monthly_views = px.line(
                            channel_monthly_views,
                            x='Month_Year',
                            y='View_count',
                            title=f'Monthly Views for {channel}',
                            labels={'Month_Year': 'Month', 'View_count': 'Views'}
                        )
                        fig_channel_monthly_views.update_traces(mode='lines+markers', line=dict(color='blue'))
                        st.plotly_chart(fig_channel_monthly_views, use_container_width=True)
                        
                        # Monthly likes for this channel
                        st.subheader(f"Monthly Likes for {channel}")
                        channel_monthly_likes = channel_data.groupby('Month_Year')['Like_count'].sum().reset_index()
                        fig_channel_monthly_likes = px.line(
                            channel_monthly_likes,
                            x='Month_Year',
                            y='Like_count',
                            title=f'Monthly Likes for {channel}',
                            labels={'Month_Year': 'Month', 'Like_count': 'Likes'}
                        )
                        fig_channel_monthly_likes.update_traces(mode='lines+markers', line=dict(color='green'))
                        st.plotly_chart(fig_channel_monthly_likes, use_container_width=True)
                        
                        # Bar chart for videos published per month
                        st.subheader(f"Videos Published per Month for {channel}")
                        videos_per_month = channel_data.groupby('Month_Year').size().reset_index(name='count')
                        fig_videos_per_month = px.bar(
                            videos_per_month,
                            x='Month_Year',
                            y='count',
                            title=f'Videos Published per Month for {channel}',
                            labels={'Month_Year': 'Month', 'count': 'Number of Videos'},
                            color_discrete_sequence=['purple']
                        )
                        st.plotly_chart(fig_videos_per_month, use_container_width=True)
                        
                        # Scatter plot for views vs likes by month
                        st.subheader(f"Views vs Likes by Month for {channel}")
                        channel_monthly_combined = pd.merge(
                            channel_monthly_views,
                            channel_monthly_likes,
                            on='Month_Year'
                        )
                        fig_scatter = px.scatter(
                            channel_monthly_combined,
                            x='View_count',
                            y='Like_count',
                            title=f'Views vs Likes by Month for {channel}',
                            labels={'View_count': 'Views', 'Like_count': 'Likes'},
                            color_discrete_sequence=['orange'],
                            size='View_count',
                            hover_data=['Month_Year']
                        )
                        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("Please select at least one channel to view channel-specific analysis.")

    # Overall Summary Table
    st.header("Overall Performance Summary")
    
    # Add category to the summary stats
    summary_stats = df_filtered.groupby(['Category', 'Channel_title']).agg({
        'View_count': ['count', 'sum', 'mean', 'max'],
        'Like_count': ['sum', 'mean', 'max']
    }).round(2)

    summary_stats.columns = [
        'Total Videos', 'Total Views', 'Avg Views', 'Max Views',
        'Total Likes', 'Avg Likes', 'Max Likes'
    ]
    summary_stats = summary_stats.reset_index()
    st.dataframe(summary_stats, use_container_width=True)

    # Monthly Summary Table
    st.header("Monthly Performance Summary")
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

    # Category-wise Monthly Summary Table
    st.header("Category-wise Monthly Performance Summary")
    category_monthly_summary = df_filtered.groupby(['Category', 'Month_Year']).agg({
        'View_count': ['sum', 'mean'],
        'Like_count': ['sum', 'mean'],
        'Title': 'count'
    }).round(2)

    category_monthly_summary.columns = [
        'Total Views', 'Avg Views Per Video',
        'Total Likes', 'Avg Likes Per Video',
        'Videos Published'
    ]
    category_monthly_summary = category_monthly_summary.reset_index()
    st.dataframe(category_monthly_summary.sort_values(['Category', 'Month_Year'], ascending=[True, False]), use_container_width=True)

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

    # Add download button for monthly summary
    monthly_csv = convert_df_to_csv(monthly_summary)
    st.download_button(
        "Download Monthly Summary as CSV",
        monthly_csv,
        "youtube_monthly_summary.csv",
        "text/csv",
        key='download-monthly-csv'
    )
    
    