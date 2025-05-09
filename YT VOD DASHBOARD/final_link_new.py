
import pandas as pd
import plotly.express as px
import io
import streamlit as st
import sys
import locale

# Set page configuration (this should be at the top)
st.set_page_config(layout="wide", page_title="YouTube Channel Analytics Dashboard")

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')


# Set the locale to handle different languages
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except:
    pass  # Fall back to default if this locale is not available



# Load data from Excel files
@st.cache_data
def load_data():
    try:
        # Paths to both Excel files
        file_path1 = r"./combined_dff_Oct24_Jan25 (1) (1).xlsx"
        file_path2 = r"./combined_dff_Jul24_Sep24 (1) (1).xlsx"
        
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
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Load channel categories
@st.cache_data
def load_channel_categories():
    # This is CSV content from your CHANNEL_LIST.csv
    csv_content = """Hindi ,English ,Business,Tak
ABP NEWS,WION,Biz Tak,Astro Tak
The Lallantop,India Today,BQ Prime,MP Tak
TIMES NOW Navbharat,CNN-News18,CNBC Awaaz.,Gujarat Tak
DD News,Republic World,CNBC-TV18,Life Tak
TV9 Bharatvarsh,NDTV,ET NOW,Food Tak
News24,MIRROR NOW,moneycontrol,Kids Tak - Nursery Rhymes & Kids Songs
Good News Today,TIMES NOW,Zee Business,Gaming Tak
TV9 Hindi News,NewsX,NDTV Profit,Cinema Tak
IndiaTV,DD INDIA,Business Today,Fit Tak
News18 India,Firstpost,Mint,Bihar Tak
Republic Bharat,CRUX,Business Standard,Aaj Tak Bangla
Zee Hindustan,,The Financial Express,Dilli Tak
Zee News,,CNBC Bajar,Crime Tak
Zee News HD,,,Duniya Tak
News Nation Digital,,,Rajasthan Tak
ABPLIVE,,,News Tak
inKhabar,,,Mumbai Tak
NDTV India,,,Sports Tak
News Nation,,,Bharat Tak
India News,,,Haryana Tak
Uncut,,,Fiiber Hindi
News18 Debate & Interview,,,UP Tak
,,,Jobs Tak
,,,India Today Conclave
,,,Chunav Aaj Tak
,,,Sports Today"""
    
    # Read CSV content
    df_channels = pd.read_csv(io.StringIO(csv_content))
    
    # Process channel categories
    categories = {}
    for col in df_channels.columns:
        # Remove any leading/trailing whitespace from category names
        clean_col = col.strip()
        # Get non-empty channel names for this category
        channels = df_channels[col].dropna().tolist()
        # Remove any leading/trailing whitespace from channel names
        channels = [ch.strip() for ch in channels if isinstance(ch, str) and ch.strip()]
        categories[clean_col] = channels
    
    return categories

# Function to determine channel category
def get_channel_category(channel_name, categories):
    for category, channels in categories.items():
        if channel_name in channels:
            return category
    return "Other"

# Load data
df = load_data()
channel_categories = load_channel_categories()

# Create a flat list of all channels from categories
all_channels_list = []
for category, channels in channel_categories.items():
    all_channels_list.extend(channels)

if df is not None:
    # Add category column to the dataframe
    df['Channel_Category'] = df['Channel_title'].apply(lambda x: get_channel_category(x, channel_categories))
    
    # Sidebar Filters
    st.sidebar.header("Filters")
    
    # Category Filter
    st.sidebar.subheader("Category Filter")
    category_options = ["All"] + list(channel_categories.keys())
    selected_category = st.sidebar.selectbox(
        "Select Category",
        category_options,
        index=0
    )
    
    # Date Range Filter
    st.sidebar.subheader("Date Range Filter")
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [df['Published_date_ist'].min(), df['Published_date_ist'].max()]
    )
    
    # Channel Filter (based on selected category)
    st.sidebar.subheader("Channel Filter")
    if selected_category == "All":
        channel_options = df['Channel_title'].unique()
    else:
        channel_options = channel_categories[selected_category]
    
    selected_channel = st.sidebar.multiselect(
        "Select Channel(s)",
        channel_options,
        default=channel_options[:5] if len(channel_options) > 5 else channel_options
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
    # First filter by category if not "All"
    if selected_category == "All":
        df_category = df
    else:
        df_category = df[df['Channel_Category'] == selected_category]
    
    # Then apply other filters
    df_filtered = df_category[
        (df_category['Channel_title'].isin(selected_channel)) & 
        (df_category['Published_date_ist'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))) & 
        (df_category['View_count'].between(view_range[0], view_range[1])) & 
        (df_category['Like_count'].between(like_range[0], like_range[1]))
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
        st.metric("Average Engagement", f"{(df_filtered['Like_count'].sum() / df_filtered['View_count'].sum() * 100):.2f}%" if df_filtered['View_count'].sum() > 0 else "0%")
    
    # Category-based Analysis
    st.header("Category-based Analysis")
    
    # Create tabs for each category
    if selected_category == "All":
        category_tabs = st.tabs(list(channel_categories.keys()))
        
        for i, tab in enumerate(category_tabs):
            category = list(channel_categories.keys())[i]
            with tab:
                # Filter data for this category
                category_data = df[df['Channel_Category'] == category]
                
                # Check if there's any data for this category
                if len(category_data) > 0:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Videos", len(category_data))
                    with col2:
                        st.metric("Total Views", f"{category_data['View_count'].sum():,}")
                    with col3:
                        st.metric("Total Likes", f"{category_data['Like_count'].sum():,}")
                    
                    # Channel comparison within category
                    st.subheader(f"Channel Comparison within {category} Category")
                    
                    # Get top channels by views
                    top_channels = category_data.groupby('Channel_title').agg({
                        'View_count': 'sum',
                        'Like_count': 'sum',
                        'Title': 'count'
                    }).reset_index()
                    top_channels.columns = ['Channel', 'Total Views', 'Total Likes', 'Video Count']
                    top_channels = top_channels.sort_values('Total Views', ascending=False)
                    
                    # Display top channels
                    st.dataframe(top_channels, use_container_width=True)
                    
                    # Bar chart for top channels
                    col1, col2 = st.columns(2)
                    with col1:
                        fig_top_views = px.bar(
                            top_channels.head(10),
                            x='Channel',
                            y='Total Views',
                            title=f'Top 10 Channels by Views in {category} Category',
                            color='Channel'
                        )
                        st.plotly_chart(fig_top_views, use_container_width=True)
                    
                    with col2:
                        fig_top_likes = px.bar(
                            top_channels.head(10),
                            x='Channel',
                            y='Total Likes',
                            title=f'Top 10 Channels by Likes in {category} Category',
                            color='Channel'
                        )
                        st.plotly_chart(fig_top_likes, use_container_width=True)
                else:
                    st.warning(f"No data available for {category} category with the current filters.")
    else:
        # Display channels for the selected category
        st.subheader(f"Channels in {selected_category} Category")
        
        # Channel comparison within category
        category_data = df_filtered[df_filtered['Channel_Category'] == selected_category]
        
        if len(category_data) > 0:
            # Get top channels by views
            top_channels = category_data.groupby('Channel_title').agg({
                'View_count': 'sum',
                'Like_count': 'sum',
                'Title': 'count'
            }).reset_index()
            top_channels.columns = ['Channel', 'Total Views', 'Total Likes', 'Video Count']
            top_channels = top_channels.sort_values('Total Views', ascending=False)
            
            # Display top channels
            st.dataframe(top_channels, use_container_width=True)
            
            # Bar chart for top channels
            col1, col2 = st.columns(2)
            with col1:
                fig_top_views = px.bar(
                    top_channels.head(10),
                    x='Channel',
                    y='Total Views',
                    title=f'Channels by Views in {selected_category} Category',
                    color='Channel'
                )
                st.plotly_chart(fig_top_views, use_container_width=True)
            
            with col2:
                fig_top_likes = px.bar(
                    top_channels.head(10),
                    x='Channel',
                    y='Total Likes',
                    title=f'Channels by Likes in {selected_category} Category',
                    color='Channel'
                )
                st.plotly_chart(fig_top_likes, use_container_width=True)
        else:
            st.warning(f"No data available for {selected_category} category with the current filters.")
    
    # Time series visualizations
    st.header("Time Series Analysis")
    
    # Create tabs for daily and monthly views
    time_tab1, time_tab2 = st.tabs(["Daily Analysis", "Monthly Analysis"])
    
    with time_tab1:
        # Views Over Time (Daily)
        st.subheader("Views Over Time by Channel (Daily)")
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
        
        # Likes Over Time (Daily)
        st.subheader("Likes Over Time by Channel (Daily)")
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
    
    with time_tab2:
        # Views Over Time (Monthly)
        st.subheader("Views Over Time by Channel (Monthly)")
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
        
        # Likes Over Time (Monthly)
        st.subheader("Likes Over Time by Channel (Monthly)")
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
        
        # Category breakdown by month
        st.subheader("Category Performance by Month")
        category_monthly = df_filtered.groupby(['Month_Year', 'Channel_Category']).agg({
            'View_count': 'sum',
            'Like_count': 'sum',
            'Title': 'count'
        }).reset_index()
        
        fig_category_monthly = px.area(
            category_monthly,
            x='Month_Year',
            y='View_count',
            color='Channel_Category',
            title='Monthly Views by Category',
            labels={'Month_Year': 'Month', 'View_count': 'Views', 'Channel_Category': 'Category'}
        )
        st.plotly_chart(fig_category_monthly, use_container_width=True)
    
    # Individual Channel Analysis
    st.header("Channel-specific Analysis")
    
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
                    category = channel_data['Channel_Category'].iloc[0] if not channel_data.empty else "Unknown"
                    st.metric("Category", category)
                
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
                        
                        # Calculate engagement metrics
                        engagement_rate = (channel_data['Like_count'].sum() / channel_data['View_count'].sum() * 100) if channel_data['View_count'].sum() > 0 else 0
                        
                        # Create statistics DataFrame
                        stats_df = pd.DataFrame({
                            'Metric': [
                                'Average Views',
                                'Maximum Views',
                                'Average Likes',
                                'Maximum Likes',
                                'Average Like/View Ratio',
                                'Best Performing Video (Views)',
                                'Total Videos',
                                'Category'
                            ],
                            'Value': [
                                f"{channel_data['View_count'].mean():,.0f}",
                                f"{channel_data['View_count'].max():,}",
                                f"{channel_data['Like_count'].mean():,.0f}",
                                f"{channel_data['Like_count'].max():,}",
                                f"{engagement_rate:.2f}%",
                                best_video,
                                len(channel_data),
                                category
                            ]
                        })
                        st.dataframe(stats_df, use_container_width=True)
                        
                        # Performance ranking within category
                        if category != "Unknown":
                            category_channels = df_filtered[df_filtered['Channel_Category'] == category]
                            channel_ranks = category_channels.groupby('Channel_title').agg({
                                'View_count': 'sum',
                                'Like_count': 'sum'
                            }).reset_index()
                            
                            # Rank by views
                            channel_ranks['View_Rank'] = channel_ranks['View_count'].rank(ascending=False)
                            # Rank by likes
                            channel_ranks['Like_Rank'] = channel_ranks['Like_count'].rank(ascending=False)
                            
                            # Get this channel's rank
                            channel_rank = channel_ranks[channel_ranks['Channel_title'] == channel]
                            
                            if not channel_rank.empty:
                                st.subheader(f"Ranking within {category} Category")
                                st.write(f"📊 **View Rank**: {int(channel_rank['View_Rank'].iloc[0])} of {len(channel_ranks)} channels")
                                st.write(f"👍 **Like Rank**: {int(channel_rank['Like_Rank'].iloc[0])} of {len(channel_ranks)} channels")
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
                    
                    # Calculate month-over-month growth
                    if len(monthly_channel_data) > 1:
                        monthly_channel_data['Views Growth'] = monthly_channel_data['Total Views'].pct_change() * 100
                        monthly_channel_data['Likes Growth'] = monthly_channel_data['Total Likes'].pct_change() * 100
                    
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
                    
                    # Growth charts if data available
                    if len(monthly_channel_data) > 1 and 'Views Growth' in monthly_channel_data.columns:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig_views_growth = px.bar(
                                monthly_channel_data.sort_values('Month'),
                                x='Month',
                                y='Views Growth',
                                title=f'Monthly Views Growth (%) for {channel}',
                                color='Views Growth',
                                color_continuous_scale=px.colors.diverging.RdBu,
                                color_continuous_midpoint=0
                            )
                            st.plotly_chart(fig_views_growth, use_container_width=True)
                        
                        with col2:
                            fig_likes_growth = px.bar(
                                monthly_channel_data.sort_values('Month'),
                                x='Month',
                                y='Likes Growth',
                                title=f'Monthly Likes Growth (%) for {channel}',
                                color='Likes Growth',
                                color_continuous_scale=px.colors.diverging.RdBu,
                                color_continuous_midpoint=0
                            )
                            st.plotly_chart(fig_likes_growth, use_container_width=True)
                
                with subtab4:
                    st.subheader(f"Performance Graphs for {channel}")
                    
                    # Daily graphs subtabs
                    graph_tab1, graph_tab2, graph_tab3 = st.tabs(["Daily Performance", "Monthly Performance", "Video Performance"])
                    
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
                        if not channel_monthly_views.empty and not channel_monthly_likes.empty:
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
                    
                    with graph_tab3:
                        # Performance by individual video
                        st.subheader(f"Individual Video Performance for {channel}")
                        
                        # Sort videos by view count
                        top_videos = channel_data.sort_values('View_count', ascending=False)[['Title', 'Published_date_ist', 'View_count', 'Like_count']]
                        
                        # Display top videos
                        st.dataframe(top_videos, use_container_width=True)
                        
                        # Bar chart for top videos
                        st.subheader("Top 10 Videos by Views")
                        fig_top_videos = px.bar(
                            top_videos.head(10),
                            x='Title',
                            y='View_count',
                            title=f'Top 10 Videos by Views for {channel}',
                            hover_data=['Published_date_ist', 'Like_count'],
                            color='View_count',
                            color_continuous_scale='Viridis'
                        )
                        fig_top_videos.update_layout(xaxis={'categoryorder':'total descending'})
                        st.plotly_chart(fig_top_videos, use_container_width=True)
                        
                        # Engagement rate by video
                        if not top_videos.empty:
                            top_videos['Engagement_Rate'] = (top_videos['Like_count'] / top_videos['View_count'] * 100).round(2)
                            
                            st.subheader("Top 10 Videos by Engagement Rate")
                            top_engagement = top_videos.sort_values('Engagement_Rate', ascending=False).head(10)
                            
                            fig_engagement = px.bar(
                                top_engagement,
                                x='Title',
                                y='Engagement_Rate',
                                title=f'Top 10 Videos by Engagement Rate for {channel}',
                                hover_data=['Published_date_ist', 'View_count', 'Like_count'],
                                color='Engagement_Rate',
                                color_continuous_scale='Viridis'
                            )
                            fig_engagement.update_layout(xaxis={'categoryorder':'total descending'})
                            st.plotly_chart(fig_engagement, use_container_width=True)
    else:
        st.warning("Please select at least one channel to view channel-specific analysis.")

    # Category Comparison
    st.header("Category Comparison")
    
    # Aggregate data by category
    category_stats = df_filtered.groupby('Channel_Category').agg({
        'View_count': ['sum', 'mean'],
        'Like_count': ['sum', 'mean'],
        'Title': 'count'
    }).reset_index()
    
    category_stats.columns = [
        'Category', 'Total Views', 'Avg Views per Video', 
        'Total Likes', 'Avg Likes per Video', 'Video Count'
    ]
    
    # Calculate engagement rate
    category_stats['Engagement Rate'] = (category_stats['Total Likes'] / category_stats['Total Views'] * 100).round(2)
    
    # Sort by total views
    category_stats = category_stats.sort_values('Total Views', ascending=False)
    
    # Display category stats
    st.dataframe(category_stats, use_container_width=True)
    
    # Visualize category comparison
    col1, col2 = st.columns(2)
    
    with col1:
        fig_category_views = px.bar(
            category_stats,
            x='Category',
            y='Total Views',
            title='Total Views by Category',
            color='Category'
        )
        st.plotly_chart(fig_category_views, use_container_width=True)
    
    with col2:
        fig_category_engagement = px.bar(
            category_stats,
            x='Category',
            y='Engagement Rate',
            title='Engagement Rate by Category',
            color='Category'
        )
        st.plotly_chart(fig_category_engagement, use_container_width=True)
    
    # Pie charts for category distribution
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pie_views = px.pie(
            category_stats,
            values='Total Views',
            names='Category',
            title='Views Distribution by Category'
        )
        st.plotly_chart(fig_pie_views, use_container_width=True)
    
    with col2:
        fig_pie_videos = px.pie(
            category_stats,
            values='Video Count',
            names='Category',
            title='Video Count Distribution by Category'
        )
        st.plotly_chart(fig_pie_videos, use_container_width=True)

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
    
    # Add category information
    channel_categories_df = df_filtered[['Channel_title', 'Channel_Category']].drop_duplicates()
    summary_stats = summary_stats.reset_index().merge(channel_categories_df, on='Channel_title')
    
    # Sort by total views
    summary_stats = summary_stats.sort_values('Total Views', ascending=False)
    
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
    
    # Calculate month-over-month growth
    if len(monthly_summary) > 1:
        monthly_summary['Views Growth'] = monthly_summary['Total Views'].pct_change() * 100
        monthly_summary['Likes Growth'] = monthly_summary['Total Likes'].pct_change() * 100
    
    st.dataframe(monthly_summary.sort_values('Month_Year', ascending=False), use_container_width=True)
    
    # Overall trend
    fig_monthly_overall = px.line(
        monthly_summary.sort_values('Month_Year'),
        x='Month_Year',
        y=['Total Views', 'Total Likes'],
        title='Monthly Performance Trends',
        labels={'Month_Year': 'Month', 'value': 'Count', 'variable': 'Metric'}
    )
    st.plotly_chart(fig_monthly_overall, use_container_width=True)

    # Export functionality
    st.header("Export Data")
    
    # Create tabs for different export options
    export_tab1, export_tab2, export_tab3 = st.tabs(["Raw Data", "Summary Data", "Category Data"])
    
    with export_tab1:
        @st.cache_data
        def convert_df_to_csv(df):
            return df.to_csv(index=False).encode('utf-8')

        csv = convert_df_to_csv(df_filtered)
        st.download_button(
            "Download Filtered Data as CSV",
            csv,
            "youtube_analytics_raw.csv",
            "text/csv",
            key='download-csv'
        )
    
    with export_tab2:
        # Monthly summary export
        monthly_csv = convert_df_to_csv(monthly_summary)
        st.download_button(
            "Download Monthly Summary as CSV",
            monthly_csv,
            "youtube_monthly_summary.csv",
            "text/csv",
            key='download-monthly-csv'
        )
        
        # Channel summary export
        channel_csv = convert_df_to_csv(summary_stats)
        st.download_button(
            "Download Channel Summary as CSV",
            channel_csv,
            "youtube_channel_summary.csv",
            "text/csv",
            key='download-channel-csv'
        )
    
    with export_tab3:
        # Category summary export
        category_csv = convert_df_to_csv(category_stats)
        st.download_button(
            "Download Category Summary as CSV",
            category_csv,
            "youtube_category_summary.csv",
            "text/csv",
            key='download-category-csv'
        )
        
        # Category monthly data
        category_monthly = df_filtered.groupby(['Month_Year', 'Channel_Category']).agg({
            'View_count': 'sum',
            'Like_count': 'sum',
            'Title': 'count'
        }).reset_index()
        category_monthly.columns = ['Month', 'Category', 'Total Views', 'Total Likes', 'Video Count']
        
        category_monthly_csv = convert_df_to_csv(category_monthly)
        st.download_button(
            "Download Category Monthly Data as CSV",
            category_monthly_csv,
            "youtube_category_monthly.csv",
            "text/csv",
            key='download-category-monthly-csv'
        )
else:
    st.error("Failed to load data. Please check file paths and try again.")
        
        

        
