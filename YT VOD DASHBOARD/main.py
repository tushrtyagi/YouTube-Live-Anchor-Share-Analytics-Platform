import panel as pn
import holoviews as hv
import pandas as pd
import numpy as np

hv.extension('bokeh')
pn.extension()

# Load Data
df = pd.read_csv("vod_data.csv")

# Widgets
channel_selector = pn.widgets.Select(name="Channel", options=list(df["Channel_title"].unique()))

# Function to Filter and Plot
def plot_data(channel):
    filtered_df = df[df["Channel_title"] == channel]
    bar_chart = hv.Bars(filtered_df, kdims=["Title"], vdims=["View_count"]).opts(
        width=800, height=400, xrotation=45, xlabel='Video', ylabel='Views')
    return bar_chart

interactive_plot = pn.bind(plot_data, channel_selector)

table = pn.widgets.DataFrame(df[['Title', 'View_count', 'Like_count', 'Comment_count']], height=300)

dashboard = pn.Column(
    "# YouTube Video Dashboard",
    channel_selector,
    interactive_plot,
    "## Video Data Table", table
)

dashboard.servable()
